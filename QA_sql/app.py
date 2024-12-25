import tkinter as tk
from tkinter import messagebox
import re
import time

# local files
from LLM import LLM_response
from prompt import SQL_question_message, question_answer_message
from db_utility import *

class app():
    def __init__(self, model_name, db_name):
        '''UI Initialization'''
        self.root = tk.Tk()
        self.root.title("SQL Q&A Tool")
        self.root.geometry("1000x600") 
        self.root.configure(bg="#f5f5f5")

        # Description
        description_label = tk.Label(
            self.root, text=f'Model Name: {model_name}    Database Name: {db_name}', 
            font=("Helvetica", 12), bg="#f5f5f5", anchor="w"
            )
        description_label.pack(fill="x", padx=10, pady=10)

        # Main frame
        main_frame = tk.Frame(self.root, bg="#f2f2f2")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame, bg="#f2f2f2")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        right_frame = tk.Frame(main_frame, bg="#f2f2f2")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left-side components
        tk.Label(left_frame, text="Response:", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(anchor="nw", pady=5)
        self.response_box = tk.Text(left_frame, wrap=tk.WORD, height=20, width=58, font=("Helvetica", 14))
        self.response_box.pack(fill=tk.BOTH)
        self.response_box.config(state=tk.DISABLED)

        tk.Label(left_frame, text="Enter Your Question:", font=("Helvetica", 14), bg="#f5f5f5").pack(anchor="nw")
        self.question_entry = tk.Text(left_frame, wrap=tk.WORD, height=5, width=58, font=("Helvetica", 14))
        self.question_entry.pack(fill=tk.BOTH, pady=5)

        # Right-side components
        tk.Label(right_frame, text="SQL Execution Result:", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(anchor="nw", pady=5)
        self.sql_result_box = tk.Text(right_frame, wrap=tk.WORD, height=20, width=58, font=("Helvetica", 14))
        self.sql_result_box.pack(fill=tk.BOTH)
        self.sql_result_box.config(state=tk.DISABLED)

        tk.Label(right_frame, text="Enter SQL Statement:", font=("Helvetica", 14), bg="#f5f5f5").pack(anchor="nw")
        self.sql_entry_box = tk.Text(right_frame, wrap=tk.WORD, height=5, width=58, font=("Helvetica", 14))
        self.sql_entry_box.pack(fill=tk.BOTH, pady=5)

        # Buttons
        generate_button = tk.Button(left_frame, text="Generate Response", font=("Helvetica", 14), bg="#4CAF50", command=self.generate_response_button)
        generate_button.pack(side="left", padx=5)

        self.extract_execute_button = tk.Button(left_frame, text="Extract & Execute SQL", font=("Helvetica", 14), bg="#4CAF50", command=self.extract_and_execute_sql_button)

        execute_button = tk.Button(right_frame, text="Execute SQL Statement", font=("Helvetica", 14), bg="#2196F3", command=self.execute_sql_button)
        execute_button.pack(side="left", padx=5)


        '''Variable initialization'''
        self.db_name = db_name
        self.model_name = model_name
        self.question = None
        self.schema_info = get_schema_info(self.db_name)


    def run(self):
        self.root.mainloop()


    def generate_response_button(self):
        """
        Function to send the question to the LLM and display the SQL response.
        """
        self.question = self.question_entry.get("1.0", tk.END).strip()

        if not self.question:
            messagebox.showwarning("Input Error", "Please enter a question.")
            return

        try:
            # disable button while generating response
            self.extract_execute_button.pack_forget()

            prompt = SQL_question_message(self.schema_info, self.question)
            
            print('Generating response...')

            self.response_box.config(state=tk.NORMAL)   # Make the box editable
            self.response_box.delete("1.0", tk.END)     #  Clear previous content
            self.response_box.update()
            
            # LLM streaming response
            for chunk in LLM_response(prompt, self.model_name, stream=True):
                self.response_box.insert(tk.END, chunk) 
                self.response_box.yview(tk.END) 
                self.response_box.update()

            self.response_box.config(state=tk.DISABLED)  # Disable editing

            # make extract sql button available
            self.extract_execute_button.pack(side="left", padx=25)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to the backend.\n{e}")


    def execute_sql_button(self, return_result=False):
        """
        Function to execute the sql statement. 

        Args:
            return_result (bool): whether return the query result or not
        
        Returns:
            str: the query result
        """
        sql_statement = self.sql_entry_box.get("1.0", tk.END).strip()  # Get text from the Text widget
        if not sql_statement:
            messagebox.showwarning("Input Error", "Please enter a SQL statement.")
            return

        try:
            query_result, col_header = execute_sql(sql_statement, self.db_name)
            table = format_output(query_result, col_header)

            self.sql_result_box.config(state=tk.NORMAL) 
            self.sql_result_box.delete("1.0", tk.END) 
            self.sql_result_box.insert(tk.END, table)
            self.sql_result_box.config(state=tk.DISABLED) 

            if return_result:
                return query_result, col_header

        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute the SQL statement.\n{e}")


    def extract_and_execute_sql_button(self):
        """
        Function to extract the sql statement from LLM response. 
        """
        response = self.response_box.get("1.0", tk.END).strip()
        if not response:
           messagebox.showwarning("Input Error", "No response available to extract.")
           return

        try:
            sql_query = re.search(r"```sql(.*?)```", response, re.DOTALL)

            if sql_query:
                extracted_sql = sql_query.group(1).strip()
            else:
                raise Exception

            self.sql_entry_box.delete("1.0", tk.END)
            self.sql_entry_box.insert(tk.END, extracted_sql)
            self.sql_entry_box.update()

            time.sleep(2)

            # execute SQL statements and retrieve the results
            query_result, _ = self.execute_sql_button(return_result=True)
            self.sql_result_box.update()

            prompt = question_answer_message(self.question, extracted_sql, query_result)

            # continue answering user's question if user click extract & execute SQL
            self.response_box.config(state=tk.NORMAL)
            self.response_box.insert(
                tk.END, 
                "\n\n--------------------------------------------------------------------------------------------------\n\nAnswer: ")

            # LLM streaming response
            for chunk in LLM_response(prompt, self.model_name, stream=True):
                self.response_box.insert(tk.END, chunk) 
                self.response_box.yview(tk.END) 
                self.response_box.update()

            self.response_box.config(state=tk.DISABLED)

            self.extract_execute_button.pack_forget()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract the SQL statement from LLM response.\n{e}")


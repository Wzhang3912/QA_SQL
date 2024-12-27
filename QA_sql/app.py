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
        self.root.geometry("1000x620") 
        self.root.configure(bg="#f5f5f5")

        # Description
        description_label = tk.Label(
            self.root, text=f'Model Name: {model_name}    Database Name: {db_name}', 
            font=("Helvetica", 12), bg="#f5f5f5", anchor="w"
            )
        description_label.pack(fill="x", padx=10, pady=10)

        self.status_label = tk.Label(
            self.root, text=f'Status: ', 
            font=("Helvetica", 12), bg="#f5f5f5", anchor="w"
            )
        self.status_label.pack(fill="x", padx=10)

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
        generate_button.place(x=5, y=480) 
            
        answer_button = tk.Button(left_frame, text="Generate Answer", font=("Helvetica", 14), bg="#4CAF50", command=self.question_answering_agent)
        answer_button.place(x=5, y=510) 

        self.extract_execute_button = tk.Button(left_frame, text="Extract & Execute SQL", font=("Helvetica", 14), bg="#4CAF50", command=self.extract_and_execute_sql_button)

        execute_button = tk.Button(right_frame, text="Execute SQL Statement", font=("Helvetica", 14), bg="#2196F3", command=self.execute_sql_button)
        execute_button.place(x=5, y=480)


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
            self.extract_execute_button.place_forget()
            self.status_label.config(text="Status: generating response...")

            prompt = SQL_question_message(self.schema_info, self.question)

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
            self.extract_execute_button.place(x=200, y=480)
            self.status_label.config(text="Status: ")

        except Exception as e:
            self.status_label.config(text="Status: ")
            messagebox.showerror("Error", f"API call error, failed to connect to LLM.\n{e}")


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
            keyword = detect_keyword(sql_statement)

            # if detected keyword, show warning
            if keyword is not None:
                result = messagebox.askokcancel(
                    "Confirmation", 
                    f"The query is attempted to perform '{keyword}' statement. Would you like to proceed?"
                )
                if not result:
                    return

            self.status_label.config(text="Status: executing SQL queries...")

            query_result, col_header = execute_sql(sql_statement, self.db_name)
            table = format_output(query_result, col_header)

            self.sql_result_box.config(state=tk.NORMAL) 
            self.sql_result_box.delete("1.0", tk.END) 
            self.sql_result_box.insert(tk.END, table)
            self.sql_result_box.config(state=tk.DISABLED) 

            self.status_label.config(text="Status: ")

            if return_result:
                return query_result, col_header

        except Exception as e:
            self.status_label.config(text="Status: ")
            messagebox.showerror("Error", f"Failed to execute the SQL statement.\n{e}")

    def extract_and_execute_sql_button(self, extracted_sql = None):
        """
        Function to extract the sql statement from LLM response. 
        """
        response = self.response_box.get("1.0", tk.END).strip()
        if not response:
           messagebox.showwarning("Input Error", "No response available to extract.")
           return

        try:
            if extracted_sql is None:
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

            prompt = question_answer_message(self.question, extracted_sql, query_result)
            
            self.status_label.config(text="Status: generating answers...")
            self.status_label.update()

            # continue answering user's question
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

            self.extract_execute_button.place_forget()
            self.status_label.config(text="Status: ")

        except Exception as e:
            self.status_label.config(text="Status: ")
            messagebox.showerror("Error", f"Failed to extract and execute SQL statement.\n{e}")

    
    def question_answering_agent(self):
        """
        Function to automatically generate resposen, extract sql statement, and answer the user's question.  

        The agent is capable to regenerate response with feedback if exception arises
        """
        MAX_RETRY = 3
        current_retry = 1
        # LLM feedback prompt
        feedback = None

        self.question = self.question_entry.get("1.0", tk.END).strip()
        if not self.question:
            messagebox.showwarning("Input Error", "Please enter a question.")
            return
        
        # LLM regenerate response
        while (current_retry <= MAX_RETRY):
            # ---generate response---
            try:
                self.status_label.config(text="Status: generating SQL queries...")
                self.status_label.update()

                prompt = SQL_question_message(self.schema_info, self.question, feedback=feedback)
                response = LLM_response(prompt, self.model_name, stream=False)
                feedback = None

            except Exception as e:
                self.status_label.config(text="Status: ")
                messagebox.showerror("Error", f"API call error, failed to connect to LLM.\n{e}")
                break
            
            try:
                # ---extract SQL---
                sql_query = re.search(r"```sql(.*?)```", response, re.DOTALL)

                if sql_query:
                    extracted_sql = sql_query.group(1).strip()
                else:
                    feedback = """
    The generated SQL query is not formatted correctly. 
    Please ensure the query is enclosed in proper SQL code block delimiters (```sql ... ```)"""
                    raise Exception
                
                # ---keyword detection---
                keyword = detect_keyword(extracted_sql)

                # raise exception if sql statement tries to do something other than query
                if keyword is not None:
                    feedback = f"""
    The generated SQL query is attempted to perform '{keyword}' statement. 
    Please ensure that queries are limited to SELECT statements only, as they should not modify the data."""
                    raise Exception

                self.response_box.config(state=tk.NORMAL)
                self.response_box.delete("1.0", tk.END)
                display_response = 'Generated SQL queries: \n\n' + extracted_sql + '\n\nExecuting queries...'
                self.response_box.insert(tk.END, display_response)

                self.extract_and_execute_sql_button(extracted_sql=extracted_sql)
                break

            except Exception as e:
                self.status_label.config(text=f"Status: generation failed for error {e}, retrying...")
                self.status_label.update()
                if feedback is None:
                    feedback = f"Generation failed for error: {e}. "
                time.sleep(3)
                current_retry += 1
                continue

        # Function to simulate steaming effect of response
        # def continue_action(response, extracted_sql):
        #     index = 0

        #     def type_next_char():
        #         """
        #         Simulates steaming effect by inserting one character at a time.
        #         """
        #         nonlocal index
        #         if index < len(response):
        #             self.response_box.insert(tk.END, response[index]) 
        #             self.response_box.yview(tk.END) 
        #             self.response_box.update()
        #             index += 1
        #             self.root.after(1, type_next_char)  # Adjust delay  
        #         else:
        #             self.response_box.config(state=tk.DISABLED)
        #             self.root.after(1, execute_and_display)

        #     def execute_and_display():
        #         """
        #         Call back function for use after displaying all queries in response
        #         """
        #         # Execute SQL queries and display result
        #         self.extract_and_execute_sql_button(extracted_sql=extracted_sql)

        #     type_next_char()


import argparse
from app import *

def main():
    parser = argparse.ArgumentParser(
        description="A SQL question-answering LLM tool."
    )
    parser.add_argument(
        "-m",
        "--model_name",
        type=str,
        required=True,
        help="LLM model to be used for.",
    )
    parser.add_argument(
        "-d",
        "--database_name",
        type=str,
        required=True,
        help="The database to connect with.",
    )

    args = parser.parse_args()

    sql_app = app(args.model_name, args.database_name)
    sql_app.run()


if __name__ == "__main__":
    main()


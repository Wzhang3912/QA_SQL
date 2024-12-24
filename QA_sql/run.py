# import sys
# from pathlib import Path
# main_path = Path(__file__).resolve().parent.parent
# if str(main_path) not in sys.path:
#     sys.path.append(str(main_path))

import argparse
from app import *

def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        description="A SQL question-answering LLM tool."
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="LLM model to be used for.",
    )
    parser.add_argument(
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


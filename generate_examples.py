import pandas as pd
import os
import sys


def generate_text_files_from_df(df_path):
    """
    Reads a CSV DataFrame from a specified path and generates text files
    in a subdirectory of the DataFrame's parent folder.

    Args:
        df_path (str): The full path to your CSV DataFrame (e.g., 'folder1/folder2/my_df.csv').
    """
    if not os.path.exists(df_path):
        print(
            f"Error: DataFrame not found at '{df_path}'. Please check the path and try again."
        )
        return

    try:
        df = pd.read_csv(df_path)
    except Exception as e:
        print(f"Error reading DataFrame from '{df_path}': {e}")
        return

    print(f"Successfully loaded DataFrame from '{df_path}'. Processing rows...")

    base_output_dir = os.path.dirname(df_path)

    for index, row in df.iterrows():
        before_content = row.get("before")
        rmv_lib_value = row.get("rmv_lib")
        repo_name = row.get("repo")
        commit_hash = row.get("commit")

        if pd.isna(rmv_lib_value) or str(rmv_lib_value).strip() == "":
            print(f"Skipping row {index} because 'rmv_lib' is empty.")
            continue

        if before_content is None or repo_name is None or commit_hash is None:
            print(
                f"Skipping row {index} due to missing 'before', 'repo', or 'commit' data."
            )
            continue

        sanitized_repo = str(repo_name).replace(os.sep, "_").replace("/", "_")
        sanitized_commit = str(commit_hash).replace(os.sep, "_").replace("/", "_")
        sanitized_rmv_lib = str(rmv_lib_value).replace(os.sep, "_").replace("/", "_")

        target_file_dir = os.path.join(
            base_output_dir, sanitized_rmv_lib, sanitized_repo
        )

        try:
            os.makedirs(target_file_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory '{target_file_dir}' for row {index}: {e}")
            continue

        filename = f"{sanitized_commit} - {index + 1}.txt"
        file_path = os.path.join(target_file_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(before_content))
            print(f"Generated: '{file_path}'")
        except IOError as e:
            print(f"Error writing file '{file_path}' for row {index}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python your_script_name.py <path_to_dataframe.csv>")
        print("Example: python generate_files.py folder1/folder2/my_df.csv")
        sys.exit(1)

    dataframe_file_path = sys.argv[1]
    generate_text_files_from_df(dataframe_file_path)

    print("\nProcess finished.")

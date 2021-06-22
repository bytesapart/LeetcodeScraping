import sys
import os
import pandas as pd
import click
from tabulate import tabulate

import apis
import session
import urls


def get_list_of_unsolved_questions(leetcode_client):
    """

    Parameters
    ----------
    leetcode_client
        The LeetCode Session Client

    Returns
    -------
    Sized
    """
    list_of_tables = pd.read_html(urls.SOLVED_GITHUB_REPO)
    leetcode_list_of_problems = leetcode_client.get_problems()
    total_solved_questions = []
    for table in list_of_tables:
        total_solved_questions.extend(table['#'].values.tolist())

    total_lc_questions = []
    question_title_slug = []
    question_title = []
    for question in leetcode_list_of_problems:
        total_lc_questions.append(question.frontend_question_id)
        question_title_slug.append(question.title_slug)
        question_title.append(question.title)

    difference_between_questions = set(total_lc_questions).difference(set(total_solved_questions))
    return [[question_id, question_title[question_id], question_title_slug[question_id]] for question_id in
            difference_between_questions]


@click.command()
@click.option('-s', '--show', default=False, type=bool,
              help='List number of leetcode questions, number of solved questions and number of unsolved questions')
@click.option('-u', '--username', default=None, type=str, help='Username of your Leetcode account')
@click.option('-p', '--password', default=None, type=str, help='Password of your Leetcode account')
def main(show, username, password):
    """
    Main function
    Returns
    -------
    0 or 1 depending on what went wrong
    """
    # ===== Step 1: Create Session and get Leetcode JSON =====
    if username is None and os.environ.get('LEETCODE_USERNAME') is None:
        raise ValueError(
            "Username cannot be blank. Either use the -u option to pass value to the script,"
            " or set the environment variable LEETCODE_USERNAME")
    if password is None and os.environ.get('LEETCODE_PASSWORD') is None:
        raise ValueError(
            "Password cannot be blank. Either use the -p option to pass value to the script,"
            " or set the environment variable LEETCODE_PASSWORD")
    leetcode_session = session.LeetCodeSession()
    leetcode_session.login(os.environ['LEETCODE_USERNAME'] if username is None else username,
                           os.environ['LEETCODE_PASSWORD'] if password is None else password)
    leetcode_client = apis.LeetCodeClient()

    # ===== Step 2: If show list is True =====
    if show is True:
        difference_with_questions = get_list_of_unsolved_questions(leetcode_client)
        print(f'Total number of unsolved questions are {len(difference_with_questions)}')
        print('The unsolved questions are:')
        print(tabulate(difference_with_questions))

    return 0


if __name__ == '__main__':
    sys.exit(main())

import sys
import os
import pandas as pd
import click
import bs4 as bs
import requests
from tabulate import tabulate

import apis
import session
import urls


def get_solution_tables():
    soup = bs.BeautifulSoup(requests.get(urls.SOLVED_GITHUB_REPO).content, 'lxml')
    html_table_list = soup.find_all('table')
    list_of_tables = pd.read_html(str(html_table_list), encoding='utf-8', header=0)

    temp_solution_filename_column = []
    table_rows = [tag.find_all('tr') for tag in html_table_list]
    for i, table in enumerate(table_rows):
        for row in table[1:]:
            all_cells = row.find_all('td')
            solution_links = ','.join([a['href'].split('/')[-1] for a in all_cells[2].find_all('a', href=True)])
            temp_solution_filename_column.append(solution_links)

        list_of_tables[i]['Solution Files'] = pd.Series(temp_solution_filename_column)
        temp_solution_filename_column =[]
        print()

    return list_of_tables


def get_list_of_unsolved_questions(leetcode_client, list_of_tables):
    """

    Parameters
    ----------
    leetcode_client
        The LeetCode Session Client

    list_of_tables
        The list of DataFrames containing all the tables in LeetCode-Solutions repo

    Returns
    -------
    Sized
    """
    leetcode_list_of_problems = leetcode_client.get_problems()
    total_solved_questions = []
    for table in list_of_tables:
        total_solved_questions.extend(table['#'].values.tolist())

    total_lc_questions = []
    questions = {}
    for question in leetcode_list_of_problems:
        total_lc_questions.append(question.frontend_question_id)
        questions[question.frontend_question_id] = [question.title_slug, question.title]

    difference_between_questions = set(total_lc_questions).difference(set(total_solved_questions))
    return [[question_id, questions[question_id][1], questions[question_id][0]] for question_id in
            difference_between_questions]


@click.command()
@click.option('-s', '--show', default=False, type=bool,
              help='List number of leetcode questions, number of solved questions and number of unsolved questions')
@click.option('-u', '--username', default=None, type=str, help='Username of your Leetcode account')
@click.option('-p', '--password', default=None, type=str, help='Password of your Leetcode account')
@click.option('-o', '--output-dir', default='output', type=str, help='Output directory to store the files')
def main(show, username, password, output_dir):
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

    list_of_tables = get_solution_tables()
    # ===== Step 2: If show list is True, then display it =====
    if show is True:
        difference_with_questions = get_list_of_unsolved_questions(leetcode_client, list_of_tables)
        print(f'Total number of unsolved questions are {len(difference_with_questions)}')
        print('The unsolved questions are:')
        print(tabulate(difference_with_questions))

    # ===== Step 3: Combine all the tables =====
    solution_table = pd.DataFrame(columns=list_of_tables[0].columns)
    for table in list_of_tables:
        solution_table = solution_table.append(table)
    solution_table.reset_index(drop=True, inplace=True)

    # ===== Step 3: Get all the problems as a "Problems" class for further sifting =====
    problems_table = []
    problems = leetcode_client.get_problems()
    for problem in problems:
        problems_table.append([problem.frontend_question_id, problem.title_slug])
    problems_table = pd.DataFrame(problems_table, columns=['#', 'Title Slug'])

    solution_table = solution_table.merge(problems_table, on='#')
    solution_table.index = solution_table['#']
    solution_table.sort_index(inplace=True)
    # leetcode_client.get_problem_detail('two-sum')
    return 0


if __name__ == '__main__':
    sys.exit(main())

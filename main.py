import sys
import os
from time import sleep
import tempfile
import pdfkit
import pandas as pd
import click
import bs4 as bs
import requests
from tabulate import tabulate
from ebooklib import epub
import epub_writer

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
        temp_solution_filename_column = []
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


def get_highlightjs_stub():
    """
    Get HighlightJS node as an etree
    Returns
    -------
    str
    """
    raw_html = '<script>'
    with open('prism.js') as f:
        text = f.read()
        raw_html = raw_html + text + '</script>'

    with open('prism-onedark.css') as f:
        text = f.read()
        raw_html = raw_html + '<style>' + text + '</style>'

    return raw_html


def get_solutions(solution_series):
    """

    Parameters
    ----------
    solution_series
        Solution Table
    Returns
    -------
    dict
    """
    solution_files = solution_series['Solution Files'].split(',')
    full_solution_files = {}
    for single_file in solution_files:
        try:
            if single_file.endswith('.cpp'):
                with open(os.path.join(os.getcwd(), 'LeetCode-Solutions', 'C++', single_file)) as f:
                    content = f.read()
                    content = '<pre class="line-numbers"><code class="language-cpp">' + content + '</code></pre>'
                    full_solution_files['C++'] = content
            elif single_file.endswith('.py'):
                with open(os.path.join(os.getcwd(), 'LeetCode-Solutions', 'Python', single_file)) as f:
                    content = f.read()
                    content = '<pre class="line-numbers"><code class="language-python">' + content + '</code></pre>'
                    full_solution_files['Python'] = content
            elif single_file.endswith('.sh'):
                with open(os.path.join(os.getcwd(), 'LeetCode-Solutions', 'Shell', single_file)) as f:
                    content = f.read()
                    content = '<pre class="line-numbers"><code class="language-bash">' + content + '</code></pre>'
                    full_solution_files['Bash'] = content
            elif single_file.endswith('.sql'):
                with open(os.path.join(os.getcwd(), 'LeetCode-Solutions', 'MySQL', single_file)) as f:
                    content = f.read()
                    content = '<pre class="line-numbers"><code class="language-sql">' + content + '</code></pre>'
                    full_solution_files['Shell'] = content
        except FileNotFoundError:
            print(f'File not found for {single_file}. Continuing!')
    return full_solution_files


def generate_epub_and_html(leetcode_client, solution_table, temp_html_dir):
    """

    Parameters
    ----------
    leetcode_client
        The leetcode client
    solution_table
        The DataFrame containing title stub to lookup and the file name to process
    temp_html_dir
        Temporary directory to store HTML files

    Returns
    -------
    list
    """
    chapters = []
    html_files = []
    highlight_stub = get_highlightjs_stub()
    for row in solution_table.iterrows():
        question_tree = leetcode_client.get_problem_detail(row[1]['Title Slug']).description
        if question_tree is None:
            i = 0
            while True:
                sleep(5)
                i = i + 1
                print(f'{row[1]["Title"]} not found. Retrying. Try number {i}')
                question_tree = leetcode_client.get_problem_detail(row[1]['Title Slug']).description
                if question_tree is not None:
                    break
        print(row[1]['Title'])
        question_tree = question_tree.replace("<pre>", "<pre><code class=\"language-plaintext\">").replace("</pre>",
                                                                                                           "</code></pre>")
        solutions = get_solutions(row[1])
        final_string = question_tree + highlight_stub

        n = len(row[1]['Title'])
        title_decorator = '*' * n
        problem_title_html = title_decorator + f'<h1 id="title">{row[1]["Title"]}</h1>' + '\n' + title_decorator + '<br><br><hr><br>'

        c = epub.EpubHtml(title=row[1]['Title'], file_name=f'chap_{row[1].name}.html', lang='en')
        c.content = problem_title_html + final_string
        chapters.append(c)

        with open(os.path.join(temp_html_dir.name, f'chap_{row[1].name}.html'), 'w') as html_chap:
            html_chap.write(problem_title_html + final_string)
        html_files.append(os.path.join(temp_html_dir.name, f'chap_{row[1].name}.html'))

        for key, solution in solutions.items():
            problem_title_html = title_decorator + f'<h1 id="title">{row[1]["Title"]}({key})</h1>' + '\n' + title_decorator + '<br><br><hr><br>'
            solution = problem_title_html + solution + highlight_stub
            c = epub.EpubHtml(title=row[1]['Title'] + '(' + key + ')',
                              file_name=f'chap_{row[1].name}_Solution({key}).html', lang='en')
            c.content = solution
            chapters.append(c)

            with open(os.path.join(temp_html_dir.name, f'chap_{row[1].name}_Solution({key}).html'), 'w') as html_chap:
                html_chap.write(solution)
            html_files.append(os.path.join(temp_html_dir.name, f'chap_{row[1].name}_Solution({key}).html'))
    return chapters, html_files


@click.command()
@click.option('-s', '--show', default=False, type=bool,
              help='List number of leetcode questions, number of solved questions and number of unsolved questions')
@click.option('-u', '--username', default=None, type=str, help='Username of your Leetcode account')
@click.option('-p', '--password', default=None, type=str, help='Password of your Leetcode account')
@click.option('-b', '--bifurcate', default=False, type=bool, help='Bifurcate on the basis of problem difficulty')
def main(show, username, password, bifurcate):
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

    list_of_tables = get_solution_tables()[1:]  # Remove the summary table
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

    temp_html_dir = tempfile.TemporaryDirectory()
    if bifurcate is True:
        solution_group = solution_table.replace('Meidum', 'Medium').groupby('Difficulty')
        for name, solution_group_table in solution_group:
            chapters, html_files = generate_epub_and_html(leetcode_client, solution_group_table.reset_index(drop=True),
                                                          temp_html_dir)
            epub_writer.write(f"Leetcode_{name}.epub", f"Leetcode {name}", "Anonymous", chapters)
            pdfkit.from_file(html_files, f"Leetcode_{name}.pdf", toc={'xsl-style-sheet': 'default.xsl'},
                             cover='cover.html', cover_first=True, options={'enable-local-file-access': ""})
    else:
        chapters, html_files = generate_epub_and_html(leetcode_client, solution_table, temp_html_dir)
        epub_writer.write("Leetcode_All.epub", "Leetcode Questions", "Anonymous", chapters)
        pdfkit.from_file(html_files, f"Leetcode_All.pdf", toc={'xsl-style-sheet': 'default.xsl'}, cover='cover.html',
                         cover_first=True, options={'enable-local-file-access': ""})
    return 0


if __name__ == '__main__':
    sys.exit(main())

import requests
import time
import csv

headers = {"Authorization": "token ###"}


class Repository:
    def __init__(self, owner, name, created_at, stars, total_closed_issues, closed_issues):
        self.owner = owner
        self.name = name
        self.created_at = created_at
        self.stars = stars
        self.total_closed_issues = total_closed_issues
        self.closed_issues = closed_issues


class Issue:
    def __init__(self, number, title, created_at, closed_at):
        self.number = number
        self.title = title
        self.created_at = created_at
        self.closed_at = closed_at


def run_query(query):
    request = requests.post('https://api.github.com/graphql',
                            json={'query': query}, headers=headers)
    while (request.status_code == 502):
        time.sleep(2)
        request = requests.post(
            'https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(
            request.status_code, query))

# Minera os repositórios


def mine(owner, name):
    # 1) Buscar os dados base que não precisam de loop
    queryBase = """
    {
    repository(owner: "%s", name: "%s") {
        createdAt
        totalIssuesFechada: issues(states:CLOSED){
            totalCount
        }
        stargazers{
            totalCount
        }
     }
    }""" % (owner, name)

    queryResultBase = run_query(queryBase)

    created_at = queryResultBase['data']['repository']['createdAt']
    stargazers = queryResultBase['data']['repository']['stargazers']['totalCount']
    # TODAS AS ISSUES FECHADAS
    total_closed_issues = queryResultBase['data']['repository']['totalIssuesFechada']['totalCount']

    repo = Repository(owner, name, created_at, stargazers, total_closed_issues, [])

    # 2) Buscar as issues do repository (loop)

    endCursor = "null"  # Proxima pagina
    closed_issues = []

    interval = total_closed_issues//50
    if interval == 0:
        interval = 1

    print('Iniciando buscas das issues do repositorio: %s, numero de repeticoes:' %
          repo.name + str(interval))
    for x in range(interval):
        # GraphQL query
        queryIssue = """
    {
        repository(owner: "%s", name: "%s") {
            issues(states: CLOSED, first: 50, after: %s) {
            pageInfo {
                endCursor
            }
            nodes {
                number
                title
                createdAt
                closedAt
            }
            }
         }
    }
    """ % (owner, name, endCursor)

        # O resultado da query que contem a proxima pagina e os nodes
        queryResultIssue = run_query(queryIssue)
        querySize = len(queryResultIssue['data']
                        ['repository']['issues']['nodes'])
        # Pega o endCursor aka proxima pagina
        endCursor = '"{}"'.format(
            queryResultIssue['data']['repository']['issues']['pageInfo']['endCursor'])

        # Monta e adiciona o obj de issue em uma lista
        for y in range(querySize):
            number = queryResultIssue['data']['repository']['issues']['nodes'][y]['number']
            title = queryResultIssue['data']['repository']['issues']['nodes'][y]['title']
            created_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['createdAt']
            closed_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['closedAt']

            # Filtra as issues apenas de um ano atrás
            if(int(created_at.rsplit('-')[0]) >= 2019):
                new_issue_from_query = Issue(
                    number, title, created_at, closed_at)

                # Salva os nodes no array de nodes
                closed_issues.append(new_issue_from_query)

        if x % 10 == 0:
            print('Loop:' + str(x))
    repo.closed_issues = closed_issues
    return repo

# Escreve em um arquivo csv


def writeCsv(repo, name):
    file_infos = "/Users/Rafael/Desktop/labex2e3/LABIII/csv_github/repos_graphql_%s.csv" % name
    with open(file_infos, 'w', encoding="utf-8") as new_file_info:

        fnames = [
            'owner',
            'name',
            'created_at',
            'stars',
            'total_closed_issues']

        csv_writer = csv.DictWriter(new_file_info, fieldnames=fnames)
        csv_writer.writeheader()
        csv_writer.writerow(
            {
                'owner': repo.owner,
                'name': repo.name,
                'created_at': repo.created_at,
                'stars': repo.stars,
                'total_closed_issues': repo.total_closed_issues
            })

        print('Arquivo csv infos gerado com sucesso!')

    print('Iniciando geração do csv de issues')
    file_issues = "/Users/Rafael/Desktop/labex2e3/LABIII/csv_github/repos_graphql_%s_issues.csv" % name
    with open(file_issues, 'w', encoding="utf-8") as new_file_issues:
        fnames = [
            'number',
            'title',
            'created_at',
            'closed_at']

        csv_writer = csv.DictWriter(new_file_issues, fieldnames=fnames)
        csv_writer.writeheader()

        for issue in repo.closed_issues:
            csv_writer.writerow(
                {
                    'number': issue.number,
                    'title': issue.title,
                    'created_at': issue.created_at,
                    'closed_at': issue.closed_at,
                })

        print('Arquivo csv issues gerado com sucesso!')


owners = ['expressjs', 'gin-gonic', 'django', 'rails', 'playframework',
          'ktorio', 'dotnet', 'spring-projects', 'vapor', 'laravel']
names = ['express', 'gin', 'django', 'rails', 'playframework',
         'ktor', 'core', 'spring-framework', 'vapor', 'laravel']


for x in range(10):
    repo = mine(owners[x], names[x])
    writeCsv(repo, names[x])
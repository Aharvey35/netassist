import requests
import webbrowser
from bs4 import BeautifulSoup
import urllib.parse


def google_search(query, site=None, top=3):
    headers = {'User-Agent': 'Mozilla/5.0'}
    encoded_query = urllib.parse.quote_plus(query)

    if site:
        encoded_query += f"+site:{site}"

    url = f"https://www.google.com/search?q={encoded_query}"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    results = []
    for g in soup.find_all('div', class_='tF2Cxc')[:top]:
        title = g.find('h3')
        link = g.find('a')
        if title and link:
            results.append((title.text.strip(), link['href']))

    return results


def run_search(args):
    query = []
    open_browser = False
    top = 3
    target_site = None

    flags = {
        '--so': 'stackoverflow.com',
        '--gh': 'github.com',
        '--cisco': 'cisco.com',
        '--csf': 'community.cisco.com',
        '--ddg': None,  # Reserved for future
    }

    for arg in args:
        if arg.startswith('--'):
            if arg == '--open':
                open_browser = True
            elif arg.startswith('--top'):
                try:
                    top = int(arg.split()[1])
                except:
                    pass
            elif arg in flags:
                target_site = flags[arg]
        else:
            query.append(arg)

    full_query = ' '.join(query)
    results = google_search(full_query, site=target_site, top=top)

    if not results:
        print("[-] No results found.")
        return

    for i, (title, link) in enumerate(results, 1):
        print(f"[{i}] {title}\n     {link}\n")
        if open_browser and i == 1:
            webbrowser.open(link)


if __name__ == "__main__":
    import sys
    run_search(sys.argv[1:])

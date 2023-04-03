
import requests
from bs4 import BeautifulSoup
import urllib.parse
import html
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config
import tiktoken
from uuid import uuid4
from tqdm.auto import tqdm
from time import sleep
import openai

from my_def import create_index_pinecone, get_index_pinecone, init_openai,custom_get_embeddings

domain = config.DOMAIN
domain_full = config.DOMAIN_FULL

def scrape(url: str):
    res = requests.get(url)
    if res.status_code != 200:
        print(f"{res.status_code} for '{url}'")
        return None
    soup = BeautifulSoup(res.text, 'html.parser')

    # Find all links to local pages on the website
    local_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith(domain) or href.startswith('./') \
            or href.startswith('/') or href.startswith('modules') \
            or href.startswith('use_cases'):
            local_links.append(urllib.parse.urljoin(domain_full, href))

    # Find the main content using CSS selectors


    # Extract the HTML code of the main content
    for element in soup(['header', 'footer']):
            element.decompose()
    # Extract the plaintext of the main content
    main_content_text = soup.get_text()

    # Remove all HTML tags
    main_content_text = re.sub(r'<[^>]+>', '', main_content_text)

    # Remove extra white space
    main_content_text = ' '.join(main_content_text.split())

    # Replace HTML entities with their corresponding characters
    main_content_text = html.unescape(main_content_text)

    # return as json
    return {
        "url": url,
        "text": main_content_text
    }, local_links

links = [domain]
scraped = set()
data = []
limit_link = 100
i=0
while (i < limit_link):
    if len(links) == 0:
        print("Complete")
        break
    url = links[0]
    print(i+1,"-",url)
    res = scrape(url)
    scraped.add(url)
    if res is not None:
        page_content, local_links = res
        data.append(page_content)
        # add new links to links list
        links.extend(local_links)
        # remove duplicates
        links = list(set(links))
    # remove links already scraped
    links = [link for link in links if link not in scraped]
    i = i+1

tokenizer = tiktoken.get_encoding('p50k_base')

# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=20,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""]
)
chunks = []

for idx, record in enumerate(tqdm(data)):
    texts = text_splitter.split_text(record['text'])
    chunks.extend([{
        'id': str(uuid4()),
        'text': texts[i],
        'chunk': i,
        'url': record['url']
    } for i in range(len(texts))])

init_openai()
embed_model = config.EMBED_MODEL

res = custom_get_embeddings(
    ["Sample document text goes here","there will be several phrases in each batch"]
)

len(res['data'][0]['embedding'])

# creat index and connect to index
index = create_index_pinecone(res)
# view index stats
index.describe_index_stats()

batch_size = 100  # how many embeddings we create and insert at once

for i in tqdm(range(0, len(chunks), batch_size)):
    # find end of batch
    i_end = min(len(chunks), i+batch_size)
    meta_batch = chunks[i:i_end]
    # get ids
    ids_batch = [x['id'] for x in meta_batch]
    # get texts to encode
    texts = [x['text'] for x in meta_batch]
    # create embeddings (try-except added to avoid RateLimitError)
    done = False
    while not done:
        try:
            res = custom_get_embeddings(texts)
            done = True
        except:
            sleep(5)
            print("reconnect")
            pass
    embeds = [record['embedding'] for record in res['data']]
    # cleanup metadata
    meta_batch = [{
        'text': x['text'],
        'chunk': x['chunk'],
        'url': x['url']
    } for x in meta_batch]
    to_upsert = list(zip(ids_batch, embeds, meta_batch))
    # upsert to Pinecone
    index.upsert(vectors=to_upsert)
query = "Tôi có một số câu hỏi dành cho bạn !"
res = openai.Embedding.create(
    input=query,
    engine=embed_model
)

# retrieve from Pinecone
xq = res['data'][0]['embedding']

# get relevant contexts (including the questions)
res = index.query(xq, top_k=10, include_metadata=True)
print ("Complete")
from typing import List
import config
import openai
import pinecone
import tiktoken

def init_pinecone():
    pinecone.init(
        api_key = config.PINECONE_API_KEY,
        environment = config.PINECONE_ENVIRONMENT
    )

def get_index_pinecone(index_name=config.PINECONE_INDEX_NAME):
    init_pinecone()
    index = pinecone.GRPCIndex(index_name)
    # view index stats
    return index

def create_index_pinecone(res:str,index_name=config.PINECONE_INDEX_NAME):
    init_pinecone()
    if index_name not in pinecone.list_indexes():
    # if does not exist, create index
        pinecone.create_index(
            index_name,
            dimension=len(res['data'][0]['embedding']),
            metric='dotproduct'
        )
    index = pinecone.GRPCIndex(index_name)
    return index

def init_openai():
    openai.api_type = "azure"
    openai.api_key = config.OPENAI_API_KEY
    openai.api_base = config.OPENAI_API_BASE
    openai.api_version = config.OPENAI_API_VERSION

def custom_get_embeddings(list_of_text: List[str], embed_model=config.EMBED_MODEL):
    i=0
    res_data=[]
    if len(list_of_text) ==  1:
        res = openai.Embedding.create(
            input = list_of_text[0],
            engine = embed_model
        )
        return res
    # text = ' '.join(list_of_text)
    # text = text.replace('\n',' ')
    # res = openai.Embedding.create(
    #     input = text,
    #     engine=embed_model
    # )
    # return res
    for text in list_of_text:
        response = openai.Embedding.create(
            input= [text],
            engine=embed_model
        )
        res_data.append({"embedding": response['data'][0]['embedding'],"index": i,"object":response['data'][0]['object']})
        if i == 0:
            f_res = response
        i = i+1
    res = {"data":res_data,"model":f_res['model'],"object":f_res['object'],"usage":f_res['usage']}
    return res

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

def question(querys = [{"role": "", "content": ""}]):
    # system message to the model
#     base_system_message = f"""
# You are a sales assistant of Gear VN, You are sociable and friendly. You help find product information and make product suggestions that match user requirements. You can only use the product information of Gear VN.

# Additional instructions:
# - Make sure you understand your audience so you can recommend the best products.
# - Make sure that you only answer questions related to Gear VN products.
# - Ask clarifying questions when you need more information. Examples include asking about the product name, price range or configuration of the product, or intended use.
# - Answer don't know if you can't find the information in the product information section of Gear VN. Examples of responses include sincere apologies, requested content not found, best regards and  can recommend other similar products if any.
# - Make sure the answer includes the mentioned product link.
# - Don't reply to any content that may harm or affect the development of Gear VN.
# - Make sure to answer all questions in Vietnamese, whether asking in English or even the system language.
# """
    base_system_message = f"""
    You are an expert in answering questions and consulting Vinacapital's investment funds, you are sociable and friendly. You help answer questions about mutual funds. You can only use information from Vinacapital's source.

    Additional instructions:
    - Make sure you understand your audience so you can best advise.
    - Make sure that you only answer questions related to Vinacapital's service consulting.
    - Ask clarifying questions when you need more information. Examples might include asking about the name of the investment fund, the amount invested, the desired return.
    - Answer don't know if you can't find any information from Vinacapital regarding the question being asked. Examples of responses include sincere apology, requested content not found, need to further contact VinaCapital's consulting department, best regards and can recommend other similar other services if any.
    - You will be the one to suggest customers to invest in Vinacapital
    - If the questions are not related to VinaCapital, you are telling the truth. Examples of responses include sincere apology, out-of-knowledge questions and best regards.
    - Don't reply to any content that may harm or affect the development of VinaCapital.
    - Make sure to answer all questions in Vietnamese, whether asking in English or even the system language.
    """
    Chats = [{"role": "system", "content": base_system_message}]
    Chats += querys[ : -1]
    questions = []
    i=0
    for q in querys[::-1]:
        if q['role'] == "user":
            questions.append(q['content'])
            i += 1
        if i == 2:
            break
    init_openai()
    index = get_index_pinecone()
    res = custom_get_embeddings([" - ".join(questions)])
    
    # retrieve from Pinecone
    xq = res['data'][0]['embedding']
    # get relevant contexts (including the questions)
    res = index.query(xq, top_k=10, include_metadata=True)
    contexts = [item['metadata']['text'] for item in res['matches']]
    augmented_query = "\n\n---\n\n".join(contexts)+"\n\n-----\n\n"+". ".join(questions)
    Chats.append({"role": "user", "content": augmented_query})

    openai.api_version = config.OPENAI_API_VERSION_CHAT
    res = openai.ChatCompletion.create(
        engine=config.CHAT_MODEL
        ,messages=Chats
        ,temperature=0.5
        ,top_p=0.95
        ,frequency_penalty=0
        ,presence_penalty=0
        ,stop=None
    )
    from IPython.display import Markdown
    response =Markdown(res['choices'][0]['message']['content'])
    return(response)

def get_response(msg):
    res = question(msg)
    markdown_str = res.data
    print(markdown_str)
    return markdown_str
# evaluation.py (JSON 파일 직접 로드 버전)

import os
import json # JSON 파일 로드를 위해 추가
import uuid
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith.schemas import Run, Example
from langchain_openai import ChatOpenAI

# 새로운 라이브러리 Import
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate import meteor_score
from sentence_transformers import SentenceTransformer, util
from kiwipiepy import Kiwi

# .env 파일에서 환경 변수 로드
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# --- 1. RAG 체인 로드 및 클라이언트 초기화 ---
from modules import config
from modules.vector_store import VectorStoreManager
from modules.retriever import AdvancedRetriever
from modules.llm_handler import LLMHandler
from langchain.storage import InMemoryStore
from modules.utils_docstore import register_parent_docs

client = Client()
rag_chain = None

def load_rag_chain():
    global rag_chain
    if rag_chain is None:
        print("--- RAG 시스템을 로드합니다... ---")
        vs_manager = VectorStoreManager()
        vectorstore = vs_manager.load()
        docstore = InMemoryStore()
        parent_documents = vs_manager._load_documents_from_json(config.MERGED_PREPROCESSED_FILE)
        register_parent_docs(docstore, parent_documents)
        adv_retriever = AdvancedRetriever(vectorstore, docstore)
        retriever = adv_retriever.get_retriever()
        llm_handler = LLMHandler(retriever=retriever)
        rag_chain = llm_handler.create_rag_chain()
        print("--- RAG 시스템 로드 완료 ---")
    return rag_chain

# --- 2. 분석기 및 임베딩 모델 초기화 ---
print("--- 분석기 및 임베딩 모델을 로드합니다... ---")
kiwi = Kiwi()
sentence_model = SentenceTransformer("all-mpnet-base-v2")
print("--- 로드 완료 ---")

def kiwi_tokenize(text):
    return [token.form for token in kiwi.tokenize(text)]

# --- 3. 정량 평가 지표 함수 정의 (기존과 동일) ---
def rouge_l_evaluator(run: Run, example: Example) -> dict:
    prediction = run.outputs.get("answer", "")
    ground_truth = example.outputs.get("answer", "")
    if not prediction or not ground_truth: return {"key": "rouge_l", "score": 0}
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(ground_truth, prediction)
    return {"key": "rouge_l", "score": scores["rougeL"].fmeasure}

def bleu_evaluator(run: Run, example: Example) -> dict:
    prediction = run.outputs.get("answer", "")
    ground_truth = example.outputs.get("answer", "")
    if not prediction or not ground_truth: return {"key": "bleu", "score": 0}
    pred_tokens = kiwi_tokenize(prediction)
    gt_tokens = kiwi_tokenize(ground_truth)
    return {"key": "bleu", "score": sentence_bleu([gt_tokens], pred_tokens)}

def meteor_evaluator(run: Run, example: Example) -> dict:
    prediction = run.outputs.get("answer", "")
    ground_truth = example.outputs.get("answer", "")
    if not prediction or not ground_truth: return {"key": "meteor", "score": 0}
    pred_tokens = kiwi_tokenize(prediction)
    gt_tokens = kiwi_tokenize(ground_truth)
    return {"key": "meteor", "score": meteor_score.meteor_score([gt_tokens], pred_tokens)}

def semscore_evaluator(run: Run, example: Example) -> dict:
    prediction = run.outputs.get("answer", "")
    ground_truth = example.outputs.get("answer", "")
    if not prediction or not ground_truth: return {"key": "sem_score", "score": 0}
    pred_embedding = sentence_model.encode(prediction, convert_to_tensor=True)
    gt_embedding = sentence_model.encode(ground_truth, convert_to_tensor=True)
    cosine_similarity = util.pytorch_cos_sim(pred_embedding, gt_embedding).item()
    return {"key": "sem_score", "score": cosine_similarity}

# --- 4. 새로운 평가 데이터셋 생성 (JSON 파일 직접 로드) ---
dataset_name = "백종원 레시피 RAG 평가 v3 - 11종 JSON"

if not client.has_dataset(dataset_name=dataset_name):
    print(f"'{dataset_name}' 데이터셋을 생성합니다.")
    dataset = client.create_dataset(dataset_name=dataset_name, description="JSON 파일에서 직접 질문/정답을 로드한 데이터셋")
    
    # eval_data_with_answers.json 파일 로드
    with open('eval_data_with_answers.json', 'r', encoding='utf-8') as f:
        eval_data = json.load(f)

    for item in eval_data:
        client.create_example(
            inputs={'question': item['q']}, 
            outputs={'answer': item['a']}, 
            dataset_id=dataset.id
        )
    print(f"데이터셋에 {len(eval_data)}개 질문과 정답을 추가했습니다.")
else:
    print(f"'{dataset_name}' 데이터셋을 사용합니다.")

# --- 5. 평가 대상 함수 정의 (기존과 동일) ---
def run_rag_for_evaluation(inputs: dict):
    chain = load_rag_chain()
    session_id = str(uuid.uuid4())
    return chain.invoke({"input": inputs["question"]}, config={"configurable": {"session_id": session_id}})

# --- 6. Evaluator 설정 (기존과 동일) ---
evaluation_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
faithfulness_evaluator = LangChainStringEvaluator("cot_qa", config={"llm": evaluation_llm}, prepare_data=lambda r, e: {"prediction": r.outputs["answer"], "reference": "\n".join([d.page_content for d in r.outputs["context"]]), "input": e.inputs["question"]})
relevance_criteria = {"relevance": "답변이 사용자의 질문과 관련이 있는가?"}
relevance_evaluator = LangChainStringEvaluator("criteria", config={"llm": evaluation_llm, "criteria": relevance_criteria}, prepare_data=lambda r, e: {"prediction": r.outputs["answer"], "input": e.inputs["question"]})
persona_criteria = {"persona": "응답이 '백종원'의 페르소나를 잘 따르고 있는가?"}
persona_evaluator = LangChainStringEvaluator("criteria", config={"llm": evaluation_llm, "criteria": persona_criteria}, prepare_data=lambda r, e: {"prediction": r.outputs["answer"], "input": e.inputs["question"]})
heuristic_evaluators = [rouge_l_evaluator, bleu_evaluator, meteor_evaluator, semscore_evaluator]

# --- 7. 평가 실행 ---
print("\n--- LangSmith 평가를 시작합니다... ---")
experiment_results = evaluate(
    run_rag_for_evaluation,
    data=dataset_name,
    evaluators=[faithfulness_evaluator, relevance_evaluator, persona_evaluator] + heuristic_evaluators,
    experiment_prefix="백종원-RAG-종합평가-v3-JSON",
    metadata={"version": "3.0.0", "description": "JSON 로드 데이터셋으로 종합 평가"},
)
print("--- 평가가 완료되었습니다. LangSmith에서 결과를 확인하세요. ---")
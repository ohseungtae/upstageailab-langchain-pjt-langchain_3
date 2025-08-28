# /src/evaluation/evaluator.py

import os
import json
import uuid
from dotenv import load_dotenv

# LangSmith 및 관련 라이브러리
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith.schemas import Run, Example
from langchain_openai import ChatOpenAI

# 정량 평가 지표 라이브러리
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate import meteor_score
from sentence_transformers import SentenceTransformer, util
from kiwipiepy import Kiwi

# 새로운 프로젝트 구조에 맞게 import 경로 수정
from src.core import config
from src.core.pipeline import initialize_rag_pipeline

# --- 환경 변수 로드 ---
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# --- 분석기 및 임베딩 모델 전역 초기화 (메모리 효율성) ---
print("--- 평가용 분석기 및 임베딩 모델을 로드합니다... ---")
kiwi = Kiwi()
sentence_model = SentenceTransformer("all-mpnet-base-v2")
print("--- 로드 완료 ---")

def kiwi_tokenize(text):
    """텍스트를 형태소로 분리하는 헬퍼 함수"""
    return [token.form for token in kiwi.tokenize(text)]

# --- 정량 평가 지표 함수 정의 ---
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
    # ZeroDivisionError 방지를 위한 SmoothingFunction 추가
    chencherry = SmoothingFunction()
    return {"key": "bleu", "score": sentence_bleu([gt_tokens], pred_tokens, smoothing_function=chencherry.method1)}

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

def run_evaluation():
    """LangSmith 평가를 설정하고 실행하는 메인 함수"""
    client = Client()

    # pipeline.py를 통해 RAG 체인을 로드합니다.
    rag_chain = initialize_rag_pipeline()
    if not rag_chain:
        print("CRITICAL: RAG 파이프라인 초기화에 실패하여 평가를 중단합니다.")
        return

    # 평가 대상 함수를 정의합니다 (RAG 체인 호출).
    def run_rag_for_evaluation(inputs: dict):
        session_id = str(uuid.uuid4())
        return rag_chain.invoke(
            {"input": inputs["question"]},
            config={"configurable": {"session_id": session_id}}
        )

    # --- 평가 데이터셋 생성 또는 로드 ---
    dataset_name = "백종원 레시피 RAG 평가 v4"
    if not client.has_dataset(dataset_name=dataset_name):
        print(f"'{dataset_name}' 데이터셋을 생성합니다.")
        dataset = client.create_dataset(dataset_name=dataset_name, description="JSON 파일에서 로드한 평가 데이터셋")
        
        # config.py에서 경로를 가져와 사용합니다.
        with open(config.EVAL_DATASET_FILE, 'r', encoding='utf-8') as f:
            eval_data = json.load(f)

        for item in eval_data:
            client.create_example(
                inputs={'question': item['q']},
                outputs={'answer': item['a']},
                dataset_id=dataset.id
            )
        print(f"데이터셋에 {len(eval_data)}개의 질문과 정답을 추가했습니다.")
    else:
        print(f"'{dataset_name}' 데이터셋을 사용합니다.")

    # --- 정성/정량 평가자(Evaluator) 설정 ---
    evaluation_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 1. Faithfulness (생성된 답변이 제공된 컨텍스트에 얼마나 충실한가)
    faithfulness_evaluator = LangChainStringEvaluator("cot_qa", config={"llm": evaluation_llm}, prepare_data=lambda r, e: {"prediction": r.outputs["answer"], "reference": "\n".join([d.page_content for d in r.outputs["context"]]), "input": e.inputs["question"]})
    
    # 2. Relevance (답변이 사용자의 질문과 관련이 있는가) - ✨ 오류 수정된 부분 ✨
    relevance_criteria = {"relevance": "답변이 사용자의 질문과 관련이 있는가?"}
    relevance_evaluator = LangChainStringEvaluator(
        "criteria", 
        config={"llm": evaluation_llm, "criteria": relevance_criteria}, 
        prepare_data=lambda r, e: {"prediction": r.outputs["answer"], "input": e.inputs["question"]}
    )
    
    # 3. Persona (백종원의 페르소나를 잘 따르는가)
    persona_criteria = {"persona": "응답이 구수하고 친근한 '백종원'의 페르소나(성격, 말투, 형식)를 잘 따르고 있는가?"}
    persona_evaluator = LangChainStringEvaluator("criteria", config={"llm": evaluation_llm, "criteria": persona_criteria}, prepare_data=lambda r, e: {"prediction": r.outputs["answer"], "input": e.inputs["question"]})
    
    # 4. 휴리스틱(정량) 평가자 목록
    heuristic_evaluators = [rouge_l_evaluator, bleu_evaluator, meteor_evaluator, semscore_evaluator]

    # --- 평가 실행 ---
    print("\n--- LangSmith 평가를 시작합니다... ---")
    evaluate(
        run_rag_for_evaluation,
        data=dataset_name,
        evaluators=[faithfulness_evaluator, relevance_evaluator, persona_evaluator] + heuristic_evaluators,
        experiment_prefix="백종원-RAG-종합평가",
        metadata={"version": "4.0.0", "description": "리팩토링된 구조에서 종합 평가 실행"},
    )
    print("--- 평가가 완료되었습니다. LangSmith에서 결과를 확인하세요. ---")

# 이 파일이 직접 실행되는 것을 방지합니다. main.py를 통해 실행되어야 합니다.
if __name__ == "__main__":
    print("이 평가는 `python main.py evaluate` 명령어로 실행해야 합니다.")


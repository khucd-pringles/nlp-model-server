from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import re
import KEY # mykey.py에 openai api key를 입력 후, (import KEY => import mykey)로 변경
import sentiments
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from transformers import TextClassificationPipeline

app = Flask(__name__)
CORS(app)

BERT_PATH = "burningfalls/my-fine-tuned-bert"
GPT_NAME = "gpt-3.5-turbo"
GPT_OPTION = "친구, 일상대화, 반말, ';;' 뒤에 있는 감정을 답변 문장에 반영"

global text_classifier
global messages
messages = []


def load_bert():
    global text_classifier

    loaded_tokenizer = AutoTokenizer.from_pretrained(BERT_PATH)
    loaded_model = TFAutoModelForSequenceClassification.from_pretrained(BERT_PATH)

    text_classifier = TextClassificationPipeline(
        tokenizer=loaded_tokenizer,
        model=loaded_model,
        framework='tf',
        top_k=1
    )


def predict_sentiment(question):
    global text_classifier

    result = text_classifier(question)[0]
    feel_idx = int(re.sub(r'[^0-9]', '', result[0]['label']))
    feel = sentiments.Feel[feel_idx]["label"]

    return feel


def generate_answer(question, feel):
    messages.append({"role": "user", "content": question + ' ;; ' + feel})

    result = openai.ChatCompletion.create(
        model=GPT_NAME,
        messages=messages
    )   
    answer = result.choices[0].message.content

    messages.append({"role": "assistant", "content": answer})
    return answer


@app.route('/predict', methods=['POST'])
def predict():
    question = request.get_json()['text']
    feel = predict_sentiment(question)
    answer = generate_answer(question, feel)

    return jsonify({'result': answer})


if __name__ == '__main__':
    load_bert()
    messages.append({"role": "system", "content": GPT_OPTION})
    app.run()
import asyncio
import logging
from services.sentiment_analyzer import SentimentAnalyzer

async def run_evaluation():
    print("--- Starting Phase 3.2 Evaluation ---")
    
    # 1. Class Structure (2 pts)
    # Testing if we can initialize both types
    try:
        local_analyzer = SentimentAnalyzer(model_type='local')
        # external_analyzer = SentimentAnalyzer(model_type='external') # Requires API Key
        print("✅ Class Structure: Local initialization passed.")
    except Exception as e:
        print(f"❌ Class Structure failed: {e}")

    # 2. Sentiment Accuracy & Format (6 pts)
    test_text = "I absolutely love this new iPhone, it is amazing!"
    result = await local_analyzer.analyze_sentiment(test_text)
    
    # Validation: Check keys and format
    required_keys = ['sentiment_label', 'confidence_score', 'model_name']
    if all(k in result for k in required_keys) and result['sentiment_label'] in ['positive', 'negative', 'neutral']:
        print(f"✅ Structure Validation: Correct format returned. {result}")
    else:
        print("❌ Structure Validation: Format incorrect.")

    # 3. Emotion Detection (3 pts)
    emotion_result = await local_analyzer.analyze_emotion("I am so happy and joyful today!")
    if 'emotion' in emotion_result and emotion_result['confidence_score'] >= 0:
        print(f"✅ Emotion Detection: Passed. Detected: {emotion_result['emotion']}")
    else:
        print("❌ Emotion Detection: Failed.")

    # 4. Batch Processing (2 pts)
    texts = ["This is great!", "This is bad.", "I am neutral."]
    batch_results = await local_analyzer.batch_analyze(texts)
    if len(batch_results) == 3:
        print(f"✅ Batch Processing: Successfully analyzed {len(batch_results)} texts.")
    else:
        print("❌ Batch Processing: Failed.")

    # 5. Error Handling (2 pts)
    print("Testing Error Handling (Empty strings and None)...")
    error_cases = ["", None, "A" * 1000] # Empty, None, and Very Long
    for case in error_cases:
        try:
            res = await local_analyzer.analyze_sentiment(case)
            print(f"✅ Error Handling: Handled '{case[:10]}...' successfully.")
        except Exception as e:
            print(f"❌ Error Handling: Crashed on '{case}' with error: {e}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
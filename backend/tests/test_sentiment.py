import asyncio
import pytest
from services.sentiment_analyzer import SentimentAnalyzer

@pytest.mark.asyncio
async def test_sentiment_analyzer_neatly():
    # 1. Class Structure Test (2 Points)
    local_analyzer = SentimentAnalyzer(model_type='local')
    # external_analyzer = SentimentAnalyzer(model_type='external') # Uncomment when API key is set
    print("✅ Initialization successful")

    # 2. Sentiment Accuracy & Format (6 Points)
    test_cases = [
        ("I love this!", "positive"),
        ("I hate this.", "negative"),
        ("This is a table.", "neutral")
    ]
    
    correct_sentiment = 0
    for text, expected in test_cases:
        result = await local_analyzer.analyze_sentiment(text)
        
        # Structure validation
        assert "sentiment_label" in result
        assert "confidence_score" in result
        assert result["sentiment_label"] in ["positive", "negative", "neutral"]
        
        if result["sentiment_label"] == expected:
            correct_sentiment += 1
            
    print(f"✅ Sentiment Accuracy: {(correct_sentiment/len(test_cases))*100}%")

    # 3. Emotion Detection (3 Points)
    emotion_text = "I am very angry"
    emotion_result = await local_analyzer.analyze_emotion(emotion_text)
    assert emotion_result["emotion"] == "anger"
    print(f"✅ Emotion Detection: {emotion_result['emotion']} detected")

    # 4. Batch Processing (2 Points)
    batch_texts = ["Love it", "Hate it", "Maybe"]
    batch_results = await local_analyzer.batch_analyze(batch_texts)
    assert len(batch_results) == 3
    print("✅ Batch Processing successful")

    # 5. Error Handling (2 Points)
    # Long text (5000 chars)
    long_text = "word " * 1000 
    await local_analyzer.analyze_sentiment(long_text)
    # Empty string
    empty_res = await local_analyzer.analyze_sentiment("")
    assert empty_res["sentiment_label"] == "neutral"
    print("✅ Error handling verified")

if __name__ == "__main__":
    asyncio.run(test_sentiment_analyzer_neatly())
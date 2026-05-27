---
name: model-evaluator
description: Use when evaluating ML model performance, running evals on LLM outputs, choosing between models, creating evaluation datasets, measuring AI quality, or setting up automated benchmarks.
---

You are a **Model Evaluation Expert** — you measure AI/ML quality rigorously so you know exactly how well systems perform.

## ML Model Evaluation

### Classification Metrics
```python
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    average_precision_score, RocCurveDisplay, PrecisionRecallDisplay
)
import matplotlib.pyplot as plt
import numpy as np

def evaluate_classifier(model, X_test, y_test, class_names: list[str] = None):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
    
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))
    
    if y_prob is not None:
        print(f"ROC-AUC:           {roc_auc_score(y_test, y_prob):.4f}")
        print(f"Average Precision: {average_precision_score(y_test, y_prob):.4f}")
    
    # Confusion matrix
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', ax=axes[0], cmap='Blues')
    axes[0].set_title('Confusion Matrix')
    
    if y_prob is not None:
        RocCurveDisplay.from_predictions(y_test, y_prob, ax=axes[1])
        PrecisionRecallDisplay.from_predictions(y_test, y_prob, ax=axes[2])
    
    plt.tight_layout()
    plt.show()

# Class imbalance handling
from sklearn.metrics import balanced_accuracy_score
balanced_acc = balanced_accuracy_score(y_test, y_pred)
```

### Regression Metrics
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate_regressor(model, X_test, y_test):
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²:   {r2:.4f}")
    print(f"MAPE: {mape:.2f}%")
    
    # Residual plot
    residuals = y_test - y_pred
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.scatter(y_pred, residuals, alpha=0.5)
    plt.axhline(0, color='red', linestyle='--')
    plt.xlabel('Predicted'); plt.ylabel('Residuals')
    plt.title('Residual Plot')
    plt.show()
```

### Feature Importance
```python
import shap

# SHAP values (model-agnostic, best explanation)
explainer = shap.TreeExplainer(model[-1])  # Last step (actual model)
X_test_transformed = model[:-1].transform(X_test)  # Preprocessing steps
shap_values = explainer.shap_values(X_test_transformed)

# Summary plot
shap.summary_plot(shap_values, X_test_transformed, feature_names=feature_names)

# Waterfall (single prediction explanation)
shap.plots.waterfall(explainer(X_test_transformed)[0])
```

## LLM Evaluation

### Automated Evals (Framework)
```python
from anthropic import Anthropic
import json

client = Anthropic()

EVAL_DATASET = [
    {
        "input": "What is the capital of France?",
        "expected": "Paris",
        "category": "factual",
    },
    {
        "input": "Summarize this in one sentence: [long article]",
        "expected": None,  # No single right answer
        "category": "generation",
        "rubric": "Clear, accurate, under 50 words",
    },
]

def run_evals(model: str, system_prompt: str, dataset: list[dict]) -> dict:
    results = []
    
    for item in dataset:
        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": item["input"]}],
        )
        actual = response.content[0].text
        
        if item.get("expected"):
            # Exact match or keyword match
            score = 1.0 if item["expected"].lower() in actual.lower() else 0.0
        else:
            # Use LLM as judge
            score = llm_judge(item["input"], actual, item["rubric"])
        
        results.append({**item, "actual": actual, "score": score})
    
    return {
        "model": model,
        "avg_score": sum(r["score"] for r in results) / len(results),
        "by_category": {
            cat: sum(r["score"] for r in results if r["category"] == cat) /
                 sum(1 for r in results if r["category"] == cat)
            for cat in set(r["category"] for r in results)
        },
        "results": results,
    }

def llm_judge(question: str, answer: str, rubric: str) -> float:
    """Use Claude to score another model's response"""
    prompt = f"""
Rate this answer on a scale of 0-10 based on the rubric.
Question: {question}
Answer: {answer}
Rubric: {rubric}
Return ONLY a JSON object: {{"score": X, "reason": "..."}}
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    result = json.loads(response.content[0].text)
    return result["score"] / 10.0

# Compare models
for model in ["claude-haiku-4-5-20251001", "claude-sonnet-4-6", "claude-opus-4-7"]:
    results = run_evals(model, SYSTEM_PROMPT, EVAL_DATASET)
    print(f"{model}: {results['avg_score']:.3f}")
```

### Regression Testing
```python
# Ensure new prompts don't break existing functionality
def regression_test(new_system_prompt: str, baseline_scores: dict) -> bool:
    current_scores = run_evals("claude-sonnet-4-6", new_system_prompt, EVAL_DATASET)
    
    for category, baseline in baseline_scores.items():
        current = current_scores["by_category"].get(category, 0)
        if current < baseline * 0.95:  # 5% regression threshold
            print(f"❌ REGRESSION in {category}: {baseline:.3f} → {current:.3f}")
            return False
    
    print("✅ All categories within acceptable range")
    return True
```

## Evaluation Best Practices

1. **Never test on training data** — always hold out test set before EDA
2. **Stratified splits** — preserve class distribution
3. **Multiple metrics** — no single metric tells the whole story
4. **Human evaluation** — automated metrics miss nuance; sample and review manually
5. **Slice analysis** — overall metrics can hide poor performance on subgroups
6. **Calibration** — probability scores should match actual frequencies
7. **Temporal validation** — test on future data, not random split, for time-series

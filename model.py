import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import numpy as np

# Generate synthetic PHQ-9 responses for 1000 samples
np.random.seed(42)
data = np.random.randint(0, 4, (1000, 9))
df = pd.DataFrame(data, columns=[f"Q{i}" for i in range(1, 10)])

# Add total score
df['total_score'] = df.sum(axis=1)

# Label depression severity based on total_score
def get_label(score):
    if score <= 4:
        return "None"
    elif score <= 9:
        return "Mild"
    elif score <= 14:
        return "Moderate"
    elif score <= 19:
        return "Moderately Severe"
    else:
        return "Severe"

df['label'] = df['total_score'].apply(get_label)
df.drop(columns='total_score', inplace=True)

print(df.head())


X = df.drop('label', axis=1)
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print(classification_report(y_test, y_pred,zero_division=1))

import joblib
joblib.dump(model, "phq9_model.pkl")

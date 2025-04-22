import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import joblib  

df = pd.read_csv("RYDH_real_estate_data.csv")

selected_features = ['distance_to_school', 'distance_to_hospital', 'distance_to_mall',
'district_encoded', 'distance_to_park', 'distance_to_grocery','area', 'beds', 'livings', 'wc', 'category', 'street_width']

X = df[selected_features]
y = df['price'] 

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = XGBRegressor(n_estimators=300, max_depth=10, learning_rate=0.1,
                     subsample=0.8, colsample_bytree=0.8, random_state=42)
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n النتائج النهائية للنموذج:")
print(f"MAE        : {mae:.2f}")
print(f"RMSE       : {rmse:.2f}")
print(f"R² (Test)  : {r2:.4f}")

joblib.dump(model, "best_model.pkl")
joblib.dump(scaler, "scaler.pkl")

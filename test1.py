# Step 1: Import packages
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

x0=[5, 15, 25, 35, 45, 55]
y0=[5, 20, 14, 32, 22, 38]

x = np.array(x0).reshape((-1, 1))
y = np.array(y0)

model = LinearRegression()

model.fit(x,y)

r_sq = model.score(x, y)
print('coefficient of determination:', r_sq)
print('intercept:', model.intercept_)
print('slope:', float(model.coef_))

y_pred = model.predict(x)
print('predicted response:', y_pred, sep='\n')
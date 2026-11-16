import numpy as np
import pandas as pd


def detect_outliers_iqr(df: pd.DataFrame, target_col: str) -> tuple:
  """Находит выбросы в целевой переменной с помощью метода межквартильного размаха (IQR).

  """
  Q1 = df[target_col].quantile(0.25)
  Q3 = df[target_col].quantile(0.75)
  IQR = Q3 - Q1

  lower_bound = Q1 - 1.5 * IQR
  upper_bound = Q3 + 1.5 * IQR

  
  mask = (df[target_col] < lower_bound) | (df[target_col] > upper_bound)
  count = int(mask.sum())

  return mask, count


def detect_outliers_domain(df: pd.DataFrame, target_col: str) -> tuple:
  """Находит аномалии по предметному ограничению (для rank: от 1 до 200).
  """
  mask = (df[target_col] < 1) | (df[target_col] > 200)
  count = int(mask.sum())

  return mask, count
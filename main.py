# This is a sample Python script.

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# https://github.com/alan-turing-institute/sktime

# automatic FE: https://www.featuretools.com/, autofeat, gplearn
# auto FS: SelectFromModel (sklearn), Recursive Feature Elimination, Pearson correlation
# SelectKBest (Chi-2), VarianceThreshold,+
# Explaining: ELI5, LIME, SHAP

# See other tips:
# https://www.kaggle.com/vbmokin/data-science-for-tabular-data-advanced-techniques
# https://www.kaggle.com/youhanlee/simple-quant-features-using-python

import yaml

from stock.prepare_data import create_finance_dataframe
from stock.prepare_data import features_creation_lags
from stock.prepare_data import features_creation_rollings
from stock.prepare_data import features_creation_rollings_with_sliding
from stock.prepare_data import features_creation_date_extract_components

from stock.util import reduce_mem_usage
from stock.util import merge_them_all_together

from stock.model import my_model

def process_yaml():
    with open("path_data.yaml") as file:
        return yaml.safe_load(file)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    path_yaml = process_yaml()
    REDDIT_NEWS_LINK = path_yaml['news_subreddit']
    TICKERS = ["GOOG", "AMZN", "FB", "AAPL", "MSFT"]
    START = "2018-01-01"
    END = "2020-10-20"
    INTERVAL = "1d"
    PRICE = "Close"
    DATASET_FINANCE_PARAMS = dict(
        (("tickers", TICKERS), ("start", START), ("end", END),
         ("interval", INTERVAL), ("price", PRICE))
    )




    # Preview of data
    gafam_close_df = create_finance_dataframe(**DATASET_FINANCE_PARAMS)

    # Unpivot the dataframe
    stacked_df = (gafam_close_df.stack().reset_index().rename(columns={'level_1': 'Symb', 0: PRICE}))

    # Create a variable: difference between current values and 7 days_past
    stacked_df['Close_diff_14days'] = stacked_df.groupby(['Symb']).Close.pct_change(periods=14)

    # Remove "Close"
    stacked_df.drop(columns=PRICE, inplace=True)

    # Create lags, rollings, rollings with slides features and date components
    lags_df = features_creation_lags(
        stacked_df, 'Symb', 'Date', ['Close_diff_14days'], [14, 28, 42])

    rollings_df = features_creation_rollings(
        stacked_df, 'Symb', 'Date', ['Close_diff_14days'], [7, 14, 28], 14,
        ['mean', 'std', 'skew', 'kurt', 'min', 'max'])

    rollings_with_sliding_df = features_creation_rollings_with_sliding(
        stacked_df, 'Symb', 'Date', ['Close_diff_14days'],
        [7, 14, 28], [14, 28, 42], ['mean', 'std', 'skew', 'kurt', 'min', 'max'])

    date_components_df = features_creation_date_extract_components(stacked_df, 'Symb', 'Date')

    # Merge all the data + reduce the memory (useful if there is a lot of symbols)
    stacked_df = merge_them_all_together(
        stacked_df,
        [lags_df, rollings_df, rollings_with_sliding_df, date_components_df],
        ['Symb', 'Date'])

    stacked_df = reduce_mem_usage(stacked_df)

    # Remove the Nan values
    stacked_df = stacked_df.dropna()

    # Example: use only google (Do not forget to remove the origin var. to avoid data leakage)
    GOOG_df = stacked_df[stacked_df.Symb == "GOOG"].drop(columns=["Symb", "Date"]).reset_index(drop=True)
    GOOG_copy_df = GOOG_df.copy()
    GOOG_copy_df["Close_increase_14days"] = 1 * (GOOG_copy_df["Close_diff_14days"] > 0)
    GOOG_copy_df.drop(columns="Close_diff_14days", inplace=True)

    # Split the dataset into train/test
    split_size = 4 * GOOG_copy_df.__len__() // 5
    train_df, test_df = GOOG_copy_df.iloc[:split_size], GOOG_copy_df.iloc[split_size:]
    y_train, X_train = train_df['Close_increase_14days'], train_df.drop(columns=['Close_increase_14days'])
    y_test, X_test = test_df['Close_increase_14days'], test_df.drop(columns=['Close_increase_14days'])

    date_cols = ['month', 'dayofyear', 'quarter', 'dayofweek',
                 'days_in_month', 'weekofyear', 'year']

    features = [col for col in X_train.columns.to_list() if col not in date_cols]

    # Model
    clf = my_model(features)  # it's an example
    clf.fit(X_train, y_train)
    print(clf.score(X_test, y_test))  # Watch the score of your model

    # Reddit
    # Export the reddit post into the Mongo DB
    # SUBREDDIT = 'worldnews'
    # mongo_pipe = MongoDBPipeline()
    # reddit_pipe = RedditPipeline(SUBREDDIT)
    # posts = reddit_pipe.get_posts()
    # mongo_pipe.process_item(posts)

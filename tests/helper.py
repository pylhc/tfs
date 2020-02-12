def compare_dataframes(df1, df2):
    assert df1.headers == df2.headers
    for header in df1.headers:
        assert df1[header] == df2[header]
    assert all(df1.columns == df2.columns)
    for column in df1:
        assert all(df1.loc[:, column] == df2.loc[:, column])


def compare_float_dataframes(df1, df2):
    assert df1.headers == df2.headers
    for header in df1.headers:
        assert df1[header] == df2[header]
    assert all(df1.columns == df2.columns)
    for column in df1:
        assert all(abs(df1.loc[:, column] - df2.loc[:, column]) <= 1e-12)

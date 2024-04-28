from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import logging


class SignalMaster(ABC):

    def __init__(self):
        self.pkl_name = 'CL-fp.pkl'
        self.ticker_code = 'CL'
        self.contract_size = 1
        self.df2m = pd.DataFrame
        self.df3m = pd.DataFrame
        self.read_data()
        self.rolling_dates = []
        self.get_rolling_dates()
        self.rolling_ratio = self.get_rolling_weight # This is a bit slow. Do not use it in the optimisation. 
        self.ser_atr = pd.Series()
        self.get_atr()
        self.signal_price_df = self.get_signal_price_df
        
        
    def read_data(self):
        df_fp = pd.read_pickle(self.pkl_name)
        df_fp = df_fp.dropna()
        df_fp.index = pd.to_datetime(df_fp.index)
        df2m = df_fp['{}2 Comdty'.format(self.ticker_code)]
        df3m = df_fp['{}3 Comdty'.format(self.ticker_code)]
        my_cols = ['Open', 'High', 'Low', 'Close']
        df2m.columns = my_cols
        df3m.columns = my_cols

        self.df2m = df2m
        self.df3m = df3m

    def get_rolling_dates(self):
        rolling_dates = pd.read_pickle('rolling_dates.pickle')
        self.rolling_dates = rolling_dates[self.ticker_code].to_list()
    
#     @property
#     def get_rolling_weight(self):

#         def get_daily_weight(current_day):
#             relative_position = np.searchsorted(self.rolling_dates, current_day)
#             contract_end_date = self.rolling_dates[relative_position] 
#             contract_start_date = self.rolling_dates[relative_position-1]
#             month_length = (contract_end_date - contract_start_date) / pd.Timedelta('1D')
#             n_days_in_month = (current_day - contract_start_date) / pd.Timedelta('1D')
#             remind_days_in_month = (contract_end_date - current_day) / pd.Timedelta('1D')
            
#             return {'first_ratio': remind_days_in_month/month_length, 'second_ratio': n_days_in_month/month_length}
#         try:
#             output_df = pd.read_pickle('rolling_ratio_{}.pickle'.format(self.ticker_code))
#         except:
#             price_index = self.df2m.index
#             output_df = pd.DataFrame(data=[get_daily_weight(i) for i in price_index], index=price_index)
#             output_df.to_pickle('rolling_ratio_{}.pickle'.format(self.ticker_code))
        
#         return output_df

    @property
    def get_rolling_weight(self):
        
        def get_daily_weight(current_day, current_position):
            relative_position = np.searchsorted(self.rolling_dates, current_day)
            contract_end_date = self.rolling_dates[relative_position] 

            remind_days_in_month = rolling_day_position_dict[contract_end_date] - current_position

            if remind_days_in_month > 5:
                output_dict = {'first_ratio': 1, 'second_ratio': 0}
            else:
                output_dict = {'first_ratio': remind_days_in_month/5, 'second_ratio': (5-remind_days_in_month)/5}

            return output_dict
            
        price_index = self.df2m.index
        rolling_day_relative_position = np.searchsorted(price_index, self.rolling_dates)
        rolling_day_position_dict = dict(zip(self.rolling_dates, rolling_day_relative_position))

        return pd.DataFrame(data=[get_daily_weight(current_day, idx) for idx, current_day in enumerate(price_index)], 
                            index=price_index)


    def get_atr(self):
        ser_high = self.df2m['High']
        ser_low = self.df2m['Low']
        ser_close = self.df2m['Close']
        df_tmp = pd.DataFrame([], columns=['TR0', 'TR1', 'TR2'])
        df_tmp['TR0'] = abs(ser_high - ser_low)
        df_tmp['TR1'] = abs(ser_high - ser_close.shift())
        df_tmp['TR2'] = abs(ser_low - ser_close.shift())
        ser_tr = df_tmp.max(axis=1)
        ser_rolling = ser_tr.rolling(20)
        ser_atr = ser_rolling.mean()
        self.ser_atr = ser_atr.round(2)
    
    @property
    def get_signal_price_df(self):
        
        open_ser = self.df2m['Open'] * self.rolling_ratio['first_ratio'] + self.df3m['Open'] * self.rolling_ratio['second_ratio']
        close_ser = self.df2m['Close'] * self.rolling_ratio['first_ratio'] + self.df3m['Close'] * self.rolling_ratio['second_ratio']
        high_ser = self.df2m['High'] * self.rolling_ratio['first_ratio'] + self.df3m['High'] * self.rolling_ratio['second_ratio']
        low_ser = self.df2m['Low'] * self.rolling_ratio['first_ratio'] + self.df3m['Low'] * self.rolling_ratio['second_ratio']
        
        output_df = pd.concat([open_ser, close_ser, high_ser, low_ser], axis=1)
        output_df.columns = ['Open', 'Close', 'High', 'Low']
        
        return output_df
        
    
    def check_rolling(self, my_date, my_book):

        pos_fp = my_book.position('FP')

        if pos_fp != 0:
            if my_date in self.rolling_dates:
                row_m2 = self.df2m.loc[my_date]
                row_m3 = self.df3m.loc[my_date]
                my_book.trade(my_date, 'FP', -pos_fp, row_m2['Close'], self.contract_size)
                my_book.trade(my_date, 'FP', pos_fp, row_m3['Close'], self.contract_size)

                # For the print purpose
                return 1
                
    
    
    @abstractmethod
    def signal_execution_backtesting(self):
        pass


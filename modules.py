#!/usr/bin/env python
# coding: utf-8

# In[1]:
import datetime
import numpy as np
import pandas as pd

class TradingBook:
    def __init__(self, is_clean=False):
        self.ticker_dict = {}
        self.trade_list = []
        self.is_clean = is_clean
        
    # Tickers
    def tickers(self):
        my_tickers = list(self.ticker_dict.keys())
        return my_tickers  

    def del_ticker(self, ticker):
        if ticker in self.tickers():
            self.ticker_dict.pop(ticker)
            return True
        return False
              
    # Trade Log
    def trade_log(self):
        # my_tickers = list(self.ticker_dict.keys())
        df = pd.DataFrame(self.trade_list)
        return df
    
    # Profit and loss
    def total_pnl(self, ticker, price, size=1):
        my_tickers = self.tickers()
        if ticker in my_tickers:
            realized_pnl = self.get_realized_pnl(ticker)
            unrealized_pnl = self.get_unrealized_pnl(ticker, price, size)
            total_pnl = round(realized_pnl + unrealized_pnl, 3)
            return total_pnl
        else:
            return 0
    
    # Show the volume of a certain ticker
    def position(self, ticker):
        my_tickers = list(self.ticker_dict.keys())
        if ticker in my_tickers:
            return self.ticker_dict[ticker]['net_position']
        else:
            return 0
            
    #Trade
    def trade(self, ttdate, ticker, volume, price, size=1):
        if volume != 0:
            # Ticker List
            if ticker not in self.ticker_dict.keys():
                self.ticker_dict[ticker] = {
                    'net_position': 0,
                    'avg_open_price': 0,
                    'realized_pnl': 0,
                    'unrealized_pnl': 0,
                    'total_pnl': 0,
                }         
            net_pos = self.ticker_dict[ticker]['net_position']
            avg_open_price = self.ticker_dict[ticker]['avg_open_price']
            # Check if the trade is close or partially close of current position
            is_close = (net_pos * volume) < 0
            # Realized pnl
            if is_close:
                # Remember to keep the sign as the net position
                close_volume = min(abs(volume), abs(net_pos)) 
                if net_pos > 0:
                    sign_net_position = 1
                elif net_pos == 0:
                    sign_net_position = 0
                else:
                    sign_net_position = -1
                new_realized_pnl = (price - avg_open_price ) * close_volume * sign_net_position * size    
                new_realized_pnl = round(new_realized_pnl, 3)  
                self.ticker_dict[ticker]['realized_pnl'] += new_realized_pnl
                
            # avg open price
            if is_close:
                # Check if it is close-and-open
                if abs(volume) > abs(net_pos):
                    avg_open_price = price       
            else:
                net_value = avg_open_price * net_pos * size
                new_value = price * volume * size
                new_net_value = net_value + new_value
                new_net_pos = net_pos + volume
                avg_open_price = new_net_value / new_net_pos / size                      
            avg_open_price = round(avg_open_price, 4)
            self.ticker_dict[ticker]['avg_open_price'] = avg_open_price
            
            # Net position
            net_pos += volume
            self.ticker_dict[ticker]['net_position'] = net_pos

            # Clean Closed Position    
            # if self.is_clean and is_close and net_pos == 0:
            if self.is_clean and is_close: #部分Close也算Closed
                if 'Closed' not in self.ticker_dict.keys():
                    self.ticker_dict['Closed'] = {
                        'net_position': 0,
                        'avg_open_price': 0,
                        'realized_pnl': 0,
                        'unrealized_pnl': 0,
                        'total_pnl': 0,
                    }
                new_closed_pnl = self.ticker_dict[ticker]['realized_pnl']
                self.ticker_dict['Closed']['realized_pnl'] += new_closed_pnl
                self.ticker_dict['Closed']['total_pnl'] = self.ticker_dict['Closed']['realized_pnl']
                if net_pos == 0:
                    self.del_ticker(ticker)
                else:
                    self.ticker_dict[ticker]['total_pnl'] -= new_closed_pnl
                    self.ticker_dict[ticker]['realized_pnl'] = 0
        
        # Recap the trade        
        dict_deal = {'TDate':ttdate, 'Ticker':ticker, 'Volume':volume, 'Price':price, 'Value':round(volume*price, 3)}
        self.trade_list.append(dict_deal)

    def get_avg_open_price(self, ticker):
        return round(self.ticker_dict[ticker]['avg_open_price'], 4)      
        
    def get_realized_pnl(self, ticker):
        return self.ticker_dict[ticker]['realized_pnl']  
    
    def get_unrealized_pnl(self, ticker, price, size):
        avg_open_price = self.ticker_dict[ticker]['avg_open_price']
        net_pos = self.ticker_dict[ticker]['net_position'] 
        un_real_pnl = (price - avg_open_price) * net_pos * size
        un_real_pnl = round(un_real_pnl, 3)
        self.ticker_dict[ticker]['unrealized_pnl'] = un_real_pnl
        return self.ticker_dict[ticker]['unrealized_pnl']
    
    def __str__(self):
        return str(self.tickers())
    
    #Override in operator
    def __contains__(self, ticker):
        if ticker in self._book:
            return True
        else:
            return False    


class TradingDay:
    
    
    def __init__(self, turtle_data):
        # This is a cheat
        self.trading_index = turtle_data.index.sort_values()
        self.trading_index = pd.to_datetime(self.trading_index)
        self.rolling_dates = self._read_rolling_dates()
    
    def _read_rolling_dates(self):
    
        rolling_dates = pd.read_csv('FutExp.csv',index_col=0)

        rolling_dates.index = pd.to_datetime(rolling_dates.index)
        rolling_dates['CL'] = pd.to_datetime(rolling_dates['CL'])
        rolling_dates['CO'] = pd.to_datetime(rolling_dates['CO'])
        
        return rolling_dates
        
    def _get_next_month_start_day(self, input_day):
        
        input_day_year = input_day.year 
        input_day_month = input_day.month
        
        next_month_year = input_day_year + input_day_month // 12
        next_month_month = input_day_month % 12 + 1
        
        return pd.Timestamp(year=next_month_year, month=next_month_month, day=1)
    
    def get_last_trading_day(self, input_day):
        
        first_day_next_month = self._get_next_month_start_day(input_day)
        
        return self.trading_index[np.searchsorted(self.trading_index, first_day_next_month) - 1]
    
    def get_rolling_day(self, input_day, contract):
        
        rolling_days = self.rolling_dates[contract]
        
        if input_day in rolling_days:
            return True
        else:
            return False 




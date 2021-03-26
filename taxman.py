# Pseudocode
#
# 1) Load excel sheet into dataframe
# 2) Remove withdrawals
# 3) For each coin created different sheet into new file. Sort by date
# 4) For each sheet in the excel create a FIFO object named  by the coin
# 5) Take the bought currency. If it is same as FIFO object then it is a buy operation. 
#       Add at wr_poiter 0 the boughtQuantity and increment. SAve price payed and currency used
# 7) Otherwise is a sell operation.
#       Check if the date is in within 30d: if 1 it is a short term sell. Price to consider is price at position wr - 1
#                                           Otherwise is it a long term sell. Price is at position wr = 0
# 8) subtract the soldQuantity of the sell row to the boughtQuantity stored. THis is the remaining coin
# 9) substract the boughtQuantity of the sell row to the soldQuantity of the stored row. This is he gain
#10) ... 
#
#
#
#
#
#
#
#
#

import pandas as pd
from openpyxl import Workbook
import numpy as np
import os
import xlwt
from datetime import datetime, timedelta
import cryptocompare

dir_path = os.path.dirname(os.path.realpath(__file__))
print('Info: Current Directory:',dir_path)

history_file = dir_path+'/history.xls'
print('Info: Current History file:',history_file)

transaction_file = dir_path+'transactions.xls'
print('Info: Current Transaction file:',history_file)

cryptocompare.cryptocompare._set_api_key_parameter('ca7fb733c8e9c34b5ef509587fb0770233a926d00fc9de4ef4bfce4bb3451174')

class FIFO:
    def __init__(self,wr_pointer,rd_pointer):
        self.currency = None
        print('> Create a '+self.currency+' currency')
#    def add_operation(self, ):

        

total_cg = dict()
invested_euro = 0
invested_dollars = 0
# MAIN
#Create dataframe
df = pd.read_excel(history_file)
temp_df = pd.DataFrame(columns=df.columns)

cond = df.type == 'withdraw'
rows = df.loc[cond, :]

temp_df = temp_df.append(rows, ignore_index =True)

df.drop(rows.index, inplace = True)

coins_series = df['boughtCurrency']

unique_coins_list = coins_series.unique()
#print(coins_series.index)
print()



with pd.ExcelWriter('transactions.xls') as writer:
    #Create withdraw sheet
    cond = df.type == 'withdraw'
    rows = df.loc[cond, :]
    temp_df = temp_df.append(rows, ignore_index =True)
    df.drop(rows.index, inplace = True)
    temp_df.to_excel(writer, sheet_name = 'withdraw')
    temp_df = temp_df[0:0]
    #Create deposit sheet
    cond = df.type == 'deposit'
    rows = df.loc[cond, :]
    temp_df = temp_df.append(rows, ignore_index =True)
    df.drop(rows.index, inplace = True)
    temp_df.to_excel(writer, sheet_name = 'deposit')
    temp_df = temp_df[0:0]
    for coin in unique_coins_list:
        print()
        cond_buy = df.boughtCurrency == coin
        cond_sell = df.soldCurrency == coin
        rows_buy = df.loc[cond_buy,:]
        rows_sell = df.loc[cond_sell,:]
        temp_df = temp_df.append(rows_buy, ignore_index = True)
        temp_df = temp_df.append(rows_sell, ignore_index = True)
        temp_df = temp_df.sort_values('timeExecuted')
        temp_df.to_excel(writer, sheet_name = coin)
        #print(temp_df)
        print('INFO:  Creating sheet for '+coin)
        wr_pointer = 1
        cg_coin = 0
        for index,row in temp_df.iterrows():
            if row['boughtCurrency'] == coin: #buy operation
                #print(index)
                b_b_quantity = row['boughtQuantity']
                b_b_currency = coin
                b_s_quantity = row['soldQuantity']
                b_s_currency = row['soldCurrency']
                b_latest_buy = temp_df.loc[(wr_pointer-1),'boughtQuantity']
                buy_date = row['timeExecuted']
                #print(latest_buy)
                wr_pointer = wr_pointer + 1
                #print('Info: Buy operation\t',b_b_quantity,b_b_currency,b_s_quantity,b_s_currency,sep='\t')
                fifo_b_price = float(b_s_quantity)/float(b_b_quantity)
            else: #sell operation
                b_quantity = row['boughtQuantity']
                b_currency = row['boughtCurrency']
                s_quantity = row['soldQuantity']
                s_currency = coin
                sell_date = row['timeExecuted']
                latest_buy = temp_df.loc[wr_pointer-1,'boughtQuantity']
                #print(latest_buy)
                fifo_s_price = float(b_quantity)/float(s_quantity)
                remaining_coins = float(b_b_quantity) - float(s_quantity) 
                #print(coin)
                if(coin == 'USD'):
                    print('Info: No CG for dollar sell')
                    invested_dollars = invested_dollars + s_quantity
                    cg_coin = 0
                elif (coin == 'EUR'):
                    print('Info: No CG for  euro sell')
                    invested_euro = invested_euro + s_quantity
                    cg_coin = 0
                elif coin in ['USDT','USDC','UST']:
                    print('Info: CG is geglected for USDT, USDC, UST conversions')
                else:
                    print('Info: Sell operation\t',s_quantity,s_currency,b_quantity,b_currency,sep='\t')
                    print('>> BUY Price for ',coin,' = ',fifo_b_price,b_s_currency,'> SELL Price for',coin,' = ',fifo_s_price,b_currency)
                    fifo_cg = float(s_quantity)*(fifo_s_price - fifo_b_price)
                    print('>>>>: SHORT TERM CAPITAL GAIN: ',fifo_cg,b_currency)
                    cg_coin = cg_coin + fifo_cg
                    short_term = sell_date - buy_date
                    if (short_term <= timedelta(days = 31)):
                        print('>>>> :YOU buy and sell in',short_term,',so this is a SHORT term')
                        price =cryptocompare.get_historical_price_day(coin,'USD', limit=24, exchange='CCCAGG', toTs=sell_date)
                        latest_coin_price =price[0]['low']
                        print('>>>>: Price of',coin,' on',sell_date,'was',latest_coin_price)
                        latest_coin_price =price[0]['low']
                    else:
                        print('>>>>: YOU buy and sell in',short_term,',so this is a LONG term')
                        #price =cryptocompare.get_historical_price_minute(coin,'USD', limit=24, exchange='CCCAGG', toTs=datetime.now())
                        price =cryptocompare.get_historical_price_day(coin,'USD', limit=24, exchange='CCCAGG', toTs=sell_date)
                        latest_coin_price =price[0]['low']
                        print('>>>>: Price of',coin,' on',sell_date,'was',latest_coin_price)
                total_cg[coin] = cg_coin
        print('Info: TAXABLE CAPITAL GAIN',cg_coin,b_currency,'for ',coin)
        print('Info: NET GAIN at 33% taxrate = ',cg_coin*67/100,b_currency)
        print()
        temp_df = temp_df[0:0]
    keys_to_remove = ['USDT','USDC','UST']
    for item in keys_to_remove:
        del total_cg[item]
    final_cg = sum(total_cg.values())
    #print(total_cg)
    #print(price[0]['time'])
    print('Results: INVESTED EUR: ',invested_euro,' INVESTED DOLLARS: ',invested_dollars)
    print('Results: OVERALL CG =',final_cg,'.TAX to PAY =',final_cg*33/100,'.NET GAIN =',final_cg*67/100)


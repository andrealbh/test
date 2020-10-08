import random
import time
import pandas as pd
import numpy as np
import pickle

class Order:
    def __init__(self, Status, Category, Type, Size, Price, Index, Time):
        self.Status = Status # Add, Cancel, Outstanding, Executed
        self.Category = Category # Market, Limit, and for makrket order, price = 0 or max_price
        self.Type = Type # Bid, Ask
        self.Size = Size # Int
        self.Price = Price
        self.Index = Index 
        self.Time = Time
        self.ID = str(Status)[0]+str(Category)[0]+str(Type)[0]+str(Index)+str(Time)
        self.Valuation = 0

    def content(self):
        return [self.Status, self.Category, self.Type, self.Size, self.Price, self.Index, self.Time, self.ID,self.Valuation]

    def __repr__(self):
        return repr((self.Status, self.Category, self.Type, self.Size, self.Price, self.Index, self.Time))


class Order_pair:
    def __init__(self,order1,order2,price,size,time,V):
        
        self.Exe_order = order1
        self.Pair_order = order2
        self.Exe_price = price
        self.Exe_size = size
        self.Exe_time = time
        self.Exe_valuation = V[order1.Index][time]
        self.Pair_valuation = V[order2.Index][time]
        
    def content(self):
        return [self.Exe_order, self.Pair_order, self.Exe_price, self.Exe_size, self.Exe_time,self.Exe_valuation,self.Pair_valuation]

    def __repr__(self):
        
        return repr((self.Exe_order, self.Pair_order, self.Exe_price, self.Exe_size, self.Exe_time,self.Exe_valuation,self.Pair_valuation))

def Get_surplus2(pool,olist,Traders,time,V):
    s = 0
    for neworder in olist:
        pool[neworder.ID] = neworder
        

    B = []
    A = []
        
    for idk in list(pool.keys()):

        norder = pool[idk]
        agent = norder.Index
        if norder.Type == 'Bid':
            B.append(V[agent][time])

        if norder.Type == 'Ask':
            A.append(V[agent][time])


    A.sort()
    B.sort(reverse = True)

            
    lb = len(B)
    la = len(A)
    
    if lb*la != 0:
    
        for i in range(min(lb,la)):
            if B[i] >= A[i]:
                

                s += B[i] - A[i]
                #print('s',s,id1,id2,opB[i].Price,Traders[id1].Valuation,opA[i].Price,Traders[id2].Valuation)

            else:
                break
            
    return s

import random
class Trader:
    def __init__(self,types, index, asset, cash, risk, loss,strategy=[0,0,1]):
        self.Type = types
        self.Index = index
        self.Asset = asset
        self.Cash = cash
        self.Available_asset = asset
        self.Available_cash = cash
        self.Risk_bear_level = risk
        self.Max_loss = loss
        self.Order_history = []
        self.Outstanding_bid = {}
        self.Outstanding_ask = {}
        self.Outstanding_order = {}
        self.Executed_order = []
        self.Events = []
        self.Surplus = 0
        self.Valuation = 0
        self.Strategy = strategy
        
    def Pool_to_Order(self):
        self.Outstanding_bid = {}
        self.Outstanding_ask = {}
        for ID in list(self.Outstanding_order.keys()):
            order = self.Outstanding_order[ID]
            if order.Type == 'Bid':
                if order.Price in list(self.Outstanding_bid.keys()):
                    self.Outstanding_bid[order.Price].append(order.ID)
                                
                else:
                    self.Outstanding_bid[order.Price] = [order.ID]
                
            if order.Type == 'Ask':
                if order.Price in list(self.Outstanding_ask.keys()):
                    self.Outstanding_ask[order.Price].append(order.ID)
                                
                else:
                    self.Outstanding_ask[order.Price] = [order.ID]
                    
    def Place_Order(self,neworder):
        action = neworder.Status
        if action == 'Cancel':
            #print('Trader ',self.Index,' place a ',neworder,' with valuation ',neworder.Valuation,neworder.ID)
            if neworder.Type == 'Ask':
                self.Available_asset = self.Asset + neworder.Size
                    
            elif neworder.Type == 'Bid':
                self.Available_cash = self.Cash + (neworder.Size * neworder.Price)
                
            self.Outstanding_bid = {}
            self.Outstanding_ask = {}
            self.Outstanding_order = {}
            return neworder
        
        elif action == 'Add':
        
            neworder.Index = self.Index
            self.Outstanding_order[neworder.ID] = neworder
            #print('Trader ',self.Index,' place a ',neworder,neworder.ID)

            if neworder.Category == 'Limit':
                self.Outstanding_order[neworder.ID] = neworder
                if neworder.Type == 'Ask':
                    self.Available_asset = self.Asset - neworder.Size
                    
                elif neworder.Type == 'Bid':
                    self.Available_cash = self.Cash - (neworder.Size * neworder.Price)
            self.Pool_to_Order()
            
            return neworder
        
    def Update(self, order_pair,position,time):
        
        if position == 0:
        
            order = order_pair.Exe_order
            
            
        elif position == 1:
            order = order_pair.Pair_order
        ID = order.ID
            
        

        self.Outstanding_order[ID].Size -= order_pair.Exe_size
        #self.Surplus += abs(self.Valuation[time]-order_pair.Exe_price)*order_pair.Exe_size

        dead_ID = []
        if self.Outstanding_order[ID].Size == 0:
            dead_ID.append(ID)
            
        if order.Type == 'Bid':
            self.Asset += order_pair.Exe_size
            self.Cash -= (order_pair.Exe_price*order_pair.Exe_size)
            self.Surplus += (self.Valuation[time]-order_pair.Exe_price)*order_pair.Exe_size
        
        elif order.Type == 'Ask':
            self.Asset -= order_pair.Exe_size
            self.Cash += (order_pair.Exe_price*order_pair.Exe_size)
            self.Surplus += (order_pair.Exe_price-self.Valuation[time])*order_pair.Exe_size
            
        if dead_ID != []:
            for d in dead_ID:
                del self.Outstanding_order[d]
                
        self.Pool_to_Order()
        
            
    def Min_Ask_Price(self):
        asks = list(self.Outstanding_ask.keys())
        if asks == []:
            a = 100
        else:
            a = min(asks)
        return a
        
    def Max_Bid_Price(self):
        bids = list(self.Outstanding_bid.keys())
        if bids == []:
            b = 0
        else:
            b = max(bids)
        return b        
    
    def Get_Information(self):
        print('Trader ',self.Index,' holds ',self.Asset,' assets and ',self.Cash,' cash')
        print('It has outstanding orders listed ',self.Outstanding_order)
        print('Available ',self.Available_asset,self.Available_cash)    

import copy
#player_pool = {Index:Trader}

class Market:
    def __init__(self,maxprice,V):
        self.Order_Pool = {}
        self.Bid_Orders = {}
        self.Ask_Orders = {}
        self.Ask_Price = maxprice
        self.Cap = maxprice
        self.Bottom = 0
        self.Bid_Price = 0
        self.Bid_Dynamics = []
        self.Ask_Dynamics = []
        self.Surplus = 0
        self.Ture_Value = 0
        self.Value = V

        
                
        
    def Get_Ask_Price(self):
        asks = list(self.Ask_Orders.keys())
        if len(asks) > 0:
            self.Ask_Price = min(asks)
            
        else:
            self.Ask_Price = self.Cap
        
            

        
    def Get_Bid_Price(self):
        bids = list(self.Bid_Orders.keys())
        if len(bids) > 0:
            self.Bid_Price = max(bids)
            
        else:
            self.Bid_Price = self.Bottom
        

        
    def Write_into_Pool(self,order):
        self.Order_Pool[order.ID] = order
        
    def Pool_to_Book(self):
        self.Bid_Orders = {}
        self.Ask_Orders = {}
        
        for ID in list(self.Order_Pool.keys()):
    
            order = self.Order_Pool[ID]
            if order.Type == 'Bid':
                if order.Price in list(self.Bid_Orders.keys()):
                    self.Bid_Orders[order.Price].append(order.ID)
                                
                else:
                    self.Bid_Orders[order.Price] = [order.ID]
                
            if order.Type == 'Ask':
                if order.Price in list(self.Ask_Orders.keys()):
                    self.Ask_Orders[order.Price].append(order.ID)
                                
                else:
                    self.Ask_Orders[order.Price] = [order.ID]
                    
        self.Get_Ask_Price()
        self.Get_Bid_Price()
        
    def Trade(self, order, time):
        trade_result = []
        

        remaining_size = order.Size
        orders = []
        if order.Type == 'Bid':
            optional_price = list(self.Ask_Orders.keys())
            optional_price.sort()
            for p in optional_price:
                if p <= order.Price:
                    orders += self.Ask_Orders[p]
        
        else:
            optional_price = list(self.Bid_Orders.keys())
            optional_price.sort(reverse = True)
            for p in optional_price:
                if p >= order.Price:
                    orders += self.Bid_Orders[p]
                    

        dead_ID = []
        for ID in orders:
            pair = self.Order_Pool[ID]
            order_c = copy.deepcopy(order)
            
            if pair.Size <= remaining_size:
                exe_price = pair.Price
                exe_size = pair.Size
                self.Surplus += abs(order_c.Price-pair.Price)*exe_size
                order_pair = Order_pair(order_c,pair,exe_price,exe_size,time,self.Value)
                #print(order_pair)
                remaining_size -= exe_size
                trade_result.append(order_pair)
                dead_ID.append(ID)
                
            elif pair.Size > remaining_size and remaining_size > 0:
                exe_price = pair.Price
                exe_size = remaining_size
                remaining_size = 0
                pair.Size -= exe_size
                self.Surplus += abs(order_c.Price-pair.Price)*exe_size
                order_pair = Order_pair(order_c,pair,exe_price,exe_size,time,self.Value)
                #print(order_pair)
                trade_result.append(order_pair)
                break
                
            else:
                break
                
        if dead_ID != []:
            for d in dead_ID:
                del self.Order_Pool[d]
                
        if remaining_size > 0:
            order.Size = remaining_size
            self.Write_into_Pool(order)
            #trade_result.append(order)
            
        #elif remaining_size == 0:
            #trade_result.append(0)
            
        return trade_result
        
        
        
    def Update(self,order_o,time):#order_o original order
        order = copy.deepcopy(order_o)
        results = []
        if order != 0:
            if order.Status == 'Add':
                if order.Type == 'Bid':
                    if order.Price < self.Ask_Price:
                        self.Write_into_Pool(order)

                    else:
                        results = self.Trade(order,time)

                if order.Type == 'Ask':
                    if order.Price > self.Bid_Price:
                        self.Write_into_Pool(order)

                    else:
                        results = self.Trade(order,time)
                        
            if order.Status == 'Cancel':
                del self.Order_Pool[order.ID]
                
                
            self.Pool_to_Book()
            
        return results


f =  open('fl.pkl','rb')
profile = pickle.load(f)

    
num = profile['num']
P = profile['Truth']
Value = profile['valuation']

    



def Simu(maxprice,midprice,num):
    itera = 200
    Traders = {}
    agents = [i for i in range(1,num+1)]
    
    random.shuffle(agents)
    bidpro = []
    askpro = []
    tradenum = 0

    #strategies = [[0,0,1],[0,20,1],[0,50,1],[0,100,1],[20,50,1],[20,100,1],[50,100,1]]
    strategies = [[0,0,1],[0,20,1],[0,50,1],[0,100,1]]
    #strategies = [[0,0,1]]
    lstra = len(strategies)


    for i in agents[:int(num/2)]:
        print(i)
        sid = random.randint(0,lstra-1)
        Traders[i] = Trader('Seller',i,1, 1000, 0, 0, strategies[sid])
        Traders[i].Valuation = Value[i]
        
    for j in agents[int(num/2):]:

        sid = random.randint(0,lstra-1)
        Traders[j] = Trader('Buyer',j,1, 1000, 0, 0, strategies[sid])
        Traders[j].Valuation = Value[j]

    
    
            
    tot = 0
    M = Market(maxprice,Value)
    #mpool = copy.deepcopy(M.Order_Pool)
    for step in range(itera):
        
        
        mpool = copy.deepcopy(M.Order_Pool)
        lists = []
        records = []
        random.shuffle(agents)

        for ii in agents:
            #print(M.Order_Pool)
            arrive = random.randint(0,1)
            if arrive == 1:
                valuation = Traders[ii].Valuation[step]
                
                
                if len(Traders[ii].Outstanding_order.keys()) > 0:
                    for outids in Traders[ii].Outstanding_order.keys():
                        cancelorder = copy.deepcopy(Traders[ii].Outstanding_order[outids])
                        cancelorder.Status = 'Cancel'
                        Traders[ii].Place_Order(cancelorder)
                        M.Update(cancelorder,step)
                        del mpool[cancelorder.ID]
                #print(valuation)
                stra = Traders[ii].Strategy
                bid = M.Bid_Price
                asl = M.Ask_Price
                demand = random.randint(stra[0],stra[1])
                #action = random.randint(0,1)

                if Traders[ii].Type == 'Seller':
                    a = 'Ask'
                    p = valuation + demand
                    s = 1

                else:
                    a = 'Bid'
                    p = valuation - demand
                    s = 1

                order = Order('Add','Limit',a,s,p,ii,step)
                #order.Valuation = Traders[ii].Valuation
                order_c = copy.deepcopy(order)
                lists.append(order_c)
                Traders[ii].Place_Order(order)
                result = M.Update(order,step)
                bidpro.append(M.Bid_Price)
                askpro.append(M.Ask_Price)
                if result != []:
                    tradenum += len(result)
                    for epair in result:
                        a = epair.Exe_order.Index
                        b = epair.Pair_order.Index
                        Traders[a].Update(epair,0,step)
                        Traders[b].Update(epair,1,step)
                        

                records += result
                #print(M.Order_Pool)
        

        oop = copy.deepcopy(lists)
        deltatot = Get_surplus2(mpool,oop,Traders,step,Value)
        tot += deltatot
        sasur = 0
        for i in range(1,num+1):
            sasur += Traders[i].Surplus

    
        print(tot,sasur)
        
        

        
        
    asur = 0
    for i in range(1,num+1):
        asur += Traders[i].Surplus

    print(asur)
    print(tot,asur/tot)
    
    re = {}
    re['Surplus'] = asur
    re['eff'] = asur/tot
    re['bid'] = bidpro
    re['ask'] = askpro
    re['trade'] = tradenum

    
    return re

final = {}
for rounds in range(100):
	final[rounds] = Simu(1000,500,40)



f4 = open('cdafl4.pkl', 'wb')  
pickle.dump(profile, f4, -1) 



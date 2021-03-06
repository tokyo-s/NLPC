def start_process(input_text):
    from sklearn.feature_extraction.text import CountVectorizer
    import re
    import pandas as pd 
    import numpy as np 
    import matplotlib.pyplot as plt 
    import seaborn as sns
    import string
    import nltk
    import warnings 
    import twint  
    from datetime import date 
    import joblib
    import json

    def twitter_setiment_analyze(test):
        """
        This function main goal is to pre-process the data from the input dataset going through tokenization, stemming and others processes
        """
        global bow

        warnings.filterwarnings("ignore", category=DeprecationWarning)
        
        def remove_pattern(text,pattern):
            
            # re.findall() finds the pattern i.e @user and puts it in a list for further task
            r = re.findall(pattern,text)
            
            # re.sub() removes @user from the sentences in the dataset
            for i in r:
                text = re.sub(i,"",text)
            
            return text

        test['Tidy_Tweets'] = np.vectorize(remove_pattern)(test['tweet'], "@[\w]*")

        test['Tidy_Tweets'] = test['Tidy_Tweets'].str.replace("[^a-zA-Z#]", " ")

        test['Tidy_Tweets'] = test['Tidy_Tweets'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))

        tokenized_tweet = test['Tidy_Tweets'].apply(lambda x: x.split())

        from nltk import PorterStemmer

        ps = PorterStemmer()

        tokenized_tweet = tokenized_tweet.apply(lambda x: [ps.stem(i) for i in x])

        for i in range(len(tokenized_tweet)):
            tokenized_tweet[i] = ' '.join(tokenized_tweet[i])

        test['Tidy_Tweets'] = tokenized_tweet

        return test['Tidy_Tweets']

    def twiti(input_text):
        """
        This function creates a datset with tweets related to the user input
        """
        c = twint.Config()   
        wanted_item = input_text
        c.Limit = 500                  # else max 3200 tweets (intrucat selectam doar eng,  se afiseaza mai putine) 
        c.Links = "exclude"  
        c.Lang = "en" # nu lucreza :( 
        #c.Username = "sandumaiamd"   
        c.Min_likes = 2
        c.Min_retweets = 2 
        c.Min_replies  = 2     
        c.Pandas = True 
        #c.Popular_tweets = True  #doesnt really work?
        #c.Since = '2020-02-17 00:00:00'
        #c.Until = '2021-03-17 00:00:00'  

        c.Search = wanted_item
        # Run  
        c.Hide_output = True
        twint.run.Search(c) 

        df = twint.storage.panda.Tweets_df  #panda data frame
        #df #nu se afiseaza toate datele 

        tweets_list = df['tweet'].to_list()  
        lang_list = df['language'].to_list()    
        likes_list = df['nlikes'].to_list()      
        #hashtag_list =df['hashtags'].to_list()    

        postari = {}  
        postari['id'] = []
        postari['tweet'] = []
        nr = 0

        for i in range(0,len(tweets_list)): 
            if 'en' in lang_list[i]:
            # thisdict = { 'text_postare':tweets_list[i],
            #       'nr_likeuri':likes_list[i]}  
                postari['id'].append(nr)
                nr += 1
                postari['tweet'].append(tweets_list[i])
                
        # print(postari) 
        # print(len(postari))    #nr final de postari in eng 
        df = pd.DataFrame(postari) 
        df = df.set_index('id')

        return df


    #Reading the product input from the user
    input_user = input_text
    print(input_user)
    #finding results on twitter for the product input
    submission = twiti(input_user)   
     

    #Reading the Sentiment Analysis module, memorized in the joblib file
    rf = joblib.load(r'C:\Users\vladi\OneDrive\Desktop\downloads\code2\SA_module.joblib')
    #Reading the Count Vectorizer module, memorized in the joblib file
    bow = joblib.load(r'C:\Users\vladi\OneDrive\Desktop\downloads\code2\bow.joblib')

    #pre-processing the twitter dataframe
    space = bow.transform(twitter_setiment_analyze(submission))

    #predicting the results using the random forest sentiment analysis module
    test_pred = rf.predict_proba(space)

    #here we attribute to the value of test_pred_int the first column with float values of the test_pred
    test_pred_int = test_pred[:,1] 


    submission['label'] = test_pred_int
    submission1 = submission
    dataframe = submission1
    #here we ttribute the gender file input to the name variable
    names = pd.read_csv(r'C:\Users\vladi\OneDrive\Desktop\downloads\code2\gender_refine-csv.csv')
    names.dropna(inplace = True)
    names = names[0 : 17198] 
    dataframe['name'] = names['name']
    dataframe['name']

    vectorizer = CountVectorizer(analyzer='char')

    def transform(string):
        """
        This function transforms the data input
        """
        s = ''.join(i.lower() for i in string if i.isalpha())
        x = [0 for _ in range(32)]
        X = vectorizer.fit_transform([s]).toarray()
        x[26] = ord(s[0])-97
        x[27] = ord(s[-1])-97
        x[28] = len(s)
        if s[-1] in ('a','e','i','o','u'):
            x[29] = 1
        for i in s:
            if i in ('a','e','i','o','u'):
                x[30] += 1 
        x[31] = x[28] - x[30]
        count = 0
        for i in vectorizer.get_feature_names():
            x[ord(i)-97] += X[0][count]
            count += 1
        return x

    def Top_Comments(Dataframe, label = 'label', tweet = 'tweet'):
        """
        This function takes the input dataframe and returns a dictionary with some statistics about the dataframe, for example:
        Positive and negative percentage
        
        """
        dataframe.sort_values(by=[label],inplace = True)
        positive = list(dataframe.head(n = 3)[tweet])
        negative = list(dataframe.tail(n = 3)[tweet])
        top = {'Top pozitive comments':positive, 'Top negative comments':negative}
        cls = joblib.load(r'C:\Users\vladi\OneDrive\Desktop\downloads\code2\cls.joblib')
        gender = []
        for i in Dataframe['name']:
            gender.append(transform(i))
        dataframe['gender'] = cls.predict(gender).astype(np.int)
        for i in dataframe['gender'] :
            i = bool(i)
        
        dataframe.loc[dataframe.label > 0.4, 'label'] = 1
        dataframe.loc[dataframe.label <= 0.4, 'label'] = 0
        top['Number of comments'] = len(dataframe)
        top['Number of positive comments'] = len(dataframe[dataframe['label'] == 1])
        top['Number of negative comments'] = len(dataframe[dataframe['label'] == 0])
        top['Positive percent of the comments'] = round((top['Number of positive comments']/len(dataframe['label']))*100, 2)
        top['Negative percent of the comments'] = (top['Number of negative comments']/len(dataframe['label']))*100
        
        top["Number of men's comments"] = len(dataframe[dataframe['gender'] == 1])
        top["Number of men's positive comments"] = len(dataframe[(dataframe['gender'] == 1) & (dataframe['label'] == 1)])
        top["Number of men's negative comments"] = len(dataframe[(dataframe['gender'] == 1) & (dataframe['label'] == 0)])
        top["Men's comments percentage"] = (top["Number of men's comments"] / len(dataframe['label']))*100
        top["Percentage of men's positive comments"] =( top["Number of men's positive comments"] / top["Number of men's comments"])*100
        top["Percentage of men's negative comments"] = (1 - (top["Percentage of men's positive comments"]/100))*100
        
        top["Number of women's comments"] = len(dataframe[dataframe['gender'] == 0])
        top["Number of women's positive comments"] = len(dataframe[(dataframe['gender'] == 0) & (dataframe['label'] == 1)])
        top["Number of women's negative comments"] = len(dataframe[(dataframe['gender'] == 0) & (dataframe['label'] == 0)])
        top["Women's comments percentage"] = (top["Number of women's comments"] / len(dataframe['label']))*100
        top["Percentage of women's positive comments"] = (top["Number of women's positive comments"] / top["Number of women's comments"])*100
        top["Percentage of women's negative comments"] = (1 - (top["Percentage of women's positive comments"]/100))*100
         
        return top

    resum = Top_Comments(dataframe)

    test_pred_int = test_pred_int.astype(np.int)

    #Returning the result.csv with the 1/0 values
    submission['label'] = test_pred_int
    submission.to_csv(r'C:\Users\vladi\OneDrive\Desktop\downloads\code2\result.csv', index=False)
    dictionar = 'Text introductiv \n\n'
    intermediate = {key: resum[key] for key in resum.keys() & {'Number of comments', 'Number of positive comments', 'Number of negative comments', 'Positive percent of the comments'}}
    for key, value in intermediate.items():
        dictionar+=str(key) + ' : ' + str(value) + '\n'
    
    return dictionar

    

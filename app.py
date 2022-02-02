#libraries used in the script
import streamlit as st
import pandas as pd
import requests
import json
from io import StringIO

def convert_df(df):
    return df.to_csv().encode('utf-8')

st.title('Local Keyword Generator')

st.markdown(

'''Local keyword generator done by [Antoine Eripret](https://twitter.com/antoineripret). You can report a bug or an issue in [Github](https://github.com/antoineeripret/streamlit-local-keyword-generator).

You can generate keyword & get search volume from [Keyword Surfer](https://surferseo.com/keyword-surfer-extension/) or [Semrush API](https://www.semrush.com/api-analytics/). For the later, **an API key is required and you will spend 10 credits per keyword**. 

Note that these API are not perfect and if you use a better one, please reach out to me and let's talk to improve this tool :) 

''')

data = pd.read_csv('https://raw.githubusercontent.com/antoineeripret/streamlit-local-keyword-generator/main/cities1000.txt', sep='\t')
data.columns = [
                'geonameid',
                'name',
                'city',
                'alternatenames',
                'latitude',
                'longitude', 
                'feature class',
                'feature code',
                'country',
                'cc2',
                'admin1',
                'admin2',
                'admin3',
                'admin4',
                'population',
                'elevation',
                'dem',
                'timezone',
                'modification']

data = data[['city','country']]

with st.expander('STEP 1: Create your local keywords'):
    st.markdown('''
    This application use an [external city database](http://www.geonames.org/). Please pick a country below. **Country names are displayed in using their two-letters code.**.
    ''')
    country_data = st.selectbox('Choose the country', data['country'].sort_values().drop_duplicates().tolist())
    modifier = st.text_input('Choose your main keyword (e.g. hotel, restaurant, lawyer...')


with st.expander('STEP 2: Configure your extraction'):
    st.markdown('Use two letters ISO code (es,fr,de...). **Please check Keyword Surfer\'s or Semrush\'s documentation to check if your country is available.** Not all of them are. **You can indicate here a different country than what you have for STEP 1.** You can perfectly extract volumes for France for German cities for instance.')
    source = st.selectbox('Source', ('Keyword Surfer (FREE)', 'Semrush (Paid)'))
    country_api = st.text_input('Country')

    st.write('If a keyword is not included in a database, volume returned will be 0. **Which doesn\'t mean that it has no search volume ;)**')

    if source == 'Semrush (Paid)':
        semrush_api_key = st.text_input('API')

with st.expander('STEP 3: Extract Volume'):
    st.markdown('**You cannot launch this part of the tool without completing step 1 & 2 first!! Execution will fail.**')
    if st.button('Launch extraction'):
        #prepare keywords for encoding
        cities = data[data['country']==country_data]['city'].str.replace('-',' ')
        kws = modifier+' '+cities.str.lower().unique()
        #divide kws into chunks of kws
        chunks = [kws[x:x+50] for x in range(0, len(kws), 50)]
        #create dataframe to receive data from API
        results = pd.DataFrame(columns=['keyword','volume'])

        if source == 'Keyword Surfer (FREE)':
            status_bar = st.progress(0)
            #get search volume data 
            #get data 
            for i in range(0,len(chunks)):
                chunk = chunks[i]
                url = (
                    'https://db2.keywordsur.fr/keyword_surfer_keywords?country={}&keywords=[%22'.format(country_api)+
                    '%22,%22'.join(chunk)+
                    '%22]'
                )

                r = requests.get(url)
                try:
                    data = json.loads(r.text)
                except:
                    continue

                for key in data.keys():
                    results.loc[len(results)] = [key,data[key]['search_volume']]
                status_bar.progress(i/len(chunks))
            status_bar.progress(100)

            

            results = (
                pd.Series(kws)
                .to_frame()
                .rename({0:'keyword'},axis=1)
                .merge(results,on='keyword',how='left')
                .fillna(0)
            )

            st.download_button(
                "Press to download your data",
                convert_df(results),
                "file.csv",
                "text/csv",
                key='download-csv'
            )
        elif source == 'Semrush (Paid)':
            status_bar = st.progress(0)
            for i in range(len(chunks)):
                chunk = chunks[i]
                url = 'https://api.semrush.com/?type=phrase_these&key={}&export_columns=Ph,Nq&database={}&phrase={}'.format(semrush_api_key,country_api,';'.join(chunk))
                try:
                    r = requests.get(url)
                    df = pd.read_csv(StringIO(r.text), sep=';')
                    results = pd.concat([results, df.rename({'Keyword':'keyword', 'Search Volume':'volume'}, axis=1)])
                except:
                    continue
                status_bar.progress(i/len(chunks))
            status_bar.progress(100)

            
            results = (
                    pd.Series(kws)
                    .to_frame()
                    .rename({0:'keyword'},axis=1)
                    .merge(results,on='keyword',how='left')
                    .fillna(0)
                    )

            st.download_button(
                        "Press to download your data",
                        convert_df(results),
                        "file.csv",
                        "text/csv",
                        key='download-csv'
                    )
                


                


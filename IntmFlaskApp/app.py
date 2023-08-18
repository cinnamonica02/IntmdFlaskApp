from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging 
import pymongo
import requests

logging.basicConfig(filename='scrapper.log', level=logging.INFO)

app = Flask(__name__)

@app.route('/', methods=['GET'])
@cross_origin()
def homepage():
    return render_template('index.html')

@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def insdex():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")
            ipad_mini_search = 'https://www.amazon.pl/s?k=ipad+mini' + searchString
            uClient = uReq(ipad_mini_search)
            ipad_mini_page = uClient.read()
            uClient.close()
            ipad_mini_page_html = bs(ipad_mini_page, "html.parser")
            box = ipad_mini_page_html.findAll("div", {"class":"a-section a-spacing-base"})
            del box[0:3]
            boxes = box[0]
            productLink = 'https://www.amazon.pl'+ box[0].div.span.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding='utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            print(prod_html)
            commentboxes = prod_html.find_all('div', {'data-hook':'review'})

            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            reviews = []
            for commentbox in commentboxes:
                try:
                    review_url = 'https://www.amazon.pl' + commentbox.find('div').a['href']
                    logging.info("Review URL:", review_url)

                    # Extract other data you need
                    # Extract user name
                    try:
                        user_name = commentbox.find("span", class_="a-profile-name").get_text()
                    except AttributeError:
                        user_name = 'No User Name'
                    logging.info("User Name:", user_name)

                    # Extract review rating
                    try:
                        review_rating = commentbox.find("span", class_="a-icon-alt").get_text()
                    except AttributeError:
                        review_rating = 'No Rating'
                    logging.info("Review Rating:", review_rating)

                    # Extract review text
                    try:
                        review_text = commentbox.find("span", class_="review-text").get_text()
                    except AttributeError:
                        review_text = 'No Review Text'
                    logging.info("Review Text:", review_text)
                    
                    print("-" * 50)  # Separator between reviews

                except Exception as e:
                    logging.info(e)

                mydict = {'Product': searchString, 'Name': user_name, 'Rating':review_rating, 
                            'Comment': review_text 
                        }
                reviews.append(mydict)

            logging.info('log w final result {}'.format(reviews))

            # MongoDB connection and insertion
            client = pymongo.MongoClient('mongodb+srv://cinnamonica02:dodos@webscpdt1.khfzfkl.mongodb.net/?retryWrites=true&w=majority')
            db = client['amz_scrp']
            coll_create = db['ipad_mini_data']
            coll_create.insert_many(reviews)

            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            logging.info(e)
            return 'something is wrong'
    else:
        return render_template('results.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0")


# doing necessary imports
import threading

import mongoDBOperations
from logger_class import getLog
from flask import Flask, render_template, request, Response, url_for, redirect
from flask_cors import cross_origin
import pandas as pd
from mongoDBOperations import MongoDBManagement
from FlipkartScrapping import FlipkartScrapper
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import graphs

rows = {}
collection_name = None

logger = getLog('flipkart.py')

free_status = True
db_name = 'Flipkart-Scrapper'

app = Flask(__name__)  # initialising the flask app with the name 'app'

# For selenium driver implementation on heroku
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("disable-dev-shm-usage")


# To avoid the time out issue on heroku
class threadClass:

    def __init__(self, expected_review, searchString, scrapper_object, review_count):
        self.expected_review = expected_review
        self.searchString = searchString
        self.scrapper_object = scrapper_object
        self.review_count = review_count
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        global collection_name, free_status
        free_status = False
        collection_name = self.scrapper_object.getReviewsToDisplay(expected_review=self.expected_review,
                                                                   searchString=self.searchString,
                                                                   username='shayalvaghasiya',
                                                                   password='shayalvaghasiya',
                                                                   review_count=self.review_count)
        logger.info("Thread run completed")
        free_status = True


@app.route('/', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        global free_status
        ## To maintain the internal server issue on heroku
        if free_status != True:
            return "This website is executing some process. Kindly try after some time..."
        else:
            free_status = True
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        expected_review = int(request.form['expected_review'])
        try:
            review_count = 0
            scrapper_object = FlipkartScrapper(executable_path=ChromeDriverManager().install(),
                                               chrome_options=chrome_options)
            mongoClient = MongoDBManagement(username='shayalvaghasiya', password='shayalvaghasiya')
            scrapper_object.openUrl("https://www.flipkart.com/")
            logger.info("Url hitted")
            scrapper_object.login_popup_handle()
            logger.info("login popup handled")
            scrapper_object.searchProduct(searchString=searchString)
            logger.info(f"Search begins for {searchString}")
            if mongoClient.isCollectionPresent(collection_name=searchString, db_name=db_name):
                response = mongoClient.findAllRecords(db_name=db_name, collection_name=searchString)
                logger.info("Collection is already present")
                reviews = [i for i in response]
                if len(reviews) > expected_review:
                    result = [reviews[i] for i in range(0, expected_review)]
                    logger.info("Result fetched from already present collection")
                    scrapper_object.saveDataFrameToFile(file_name="static/scrapper_data.csv",
                                                        dataframe=pd.DataFrame(result))
                    logger.info("Data saved in scrapper file")
                    # scrapper_object.close_tab()
                    return render_template('results.html', rows=result)  # show the results to user
                else:
                    review_count = len(reviews)
                    threadClass(expected_review=expected_review, searchString=searchString,
                                scrapper_object=scrapper_object, review_count=review_count)
                    logger.info("data saved in scrapper file")
                    # scrapper_object.close_tab()
                    return redirect(url_for('feedback'))
            else:
                threadClass(expected_review=expected_review, searchString=searchString, scrapper_object=scrapper_object,
                            review_count=review_count)
                # scrapper_object.close_tab()
                return redirect(url_for('feedback'))

        except Exception as e:
            logger.error("Something went wrong while rendering all the details of product")
            raise Exception("(app.py) - Something went wrong while rendering all the details of product.\n" + str(e))

    else:
        return render_template('index.html')


@app.route('/feedback', methods=['GET'])
@cross_origin()
def feedback():
    try:
        global collection_name
        if collection_name is not None:
            scrapper_object = FlipkartScrapper(executable_path=ChromeDriverManager().install(),
                                               chrome_options=chrome_options)
            mongoClient = MongoDBManagement(username='shayalvaghasiya', password='shayalvaghasiya')
            rows = mongoClient.findAllRecords(db_name="Flipkart-Scrapper", collection_name=collection_name)
            reviews = [i for i in rows]
            dataframe = pd.DataFrame(reviews)
            scrapper_object.saveDataFrameToFile(file_name="static/scrapper_data.csv", dataframe=dataframe)
            collection_name = None
            return render_template('results.html', rows=reviews)
        else:
            return render_template('results.html', rows=None)
    except Exception as e:
        logger.error("Something went wrong on retrieving feedback.")
        raise Exception("(feedback) - Something went wrong on retrieving feedback.\n" + str(e))


@app.route("/graph", methods=['GET'])
@cross_origin()
def graph():
    fig = graphs.ProductReviewCountGraph()
    logger.info("graph generated")
    graph_json = fig.to_json()
    return render_template('graphs.html', graph_json=graph_json)


@app.route('/piegraph', methods=['GET', 'POST'])
@cross_origin()
def pie():
    # Connect to MongoDB server
    mongoClient = MongoDBManagement(username='shayalvaghasiya', password='shayalvaghasiya')
    database = mongoClient.getDatabase(db_name=db_name)
    # Get list of collections in the database
    collections = database.list_collection_names()
    return render_template('piegraph.html', collections=collections)

@app.route('/piechart/<collection_name>')
@cross_origin()
def pie_chart(collection_name):
    graph_html = graphs.ProductsPieChart(collection_name)
    return redirect('/' + graph_html)


if __name__ == "__main__":
    app.run()  # running the app on the local machine on port 8000

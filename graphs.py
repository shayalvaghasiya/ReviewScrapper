from mongoDBOperations import MongoDBManagement
import plotly.graph_objs as go

db_name = 'Flipkart-Scrapper'
mongoClient = MongoDBManagement(username='shayalvaghasiya', password='shayalvaghasiya')


def ProductReviewCountGraph():
    collections = mongoClient.getCollectionsList(db_name=db_name)
    document_counts = mongoClient.getDocumentCount(db_name=db_name)
    # Create a Plotly bar graph
    data = [go.Bar(
        x=collections,
        y=document_counts
    )]
    layout = go.Layout(
        title='Product vs. Review Count',
        xaxis=dict(title='Product'),
        yaxis=dict(title='Review Count')
    )
    fig = go.Figure(data=data, layout=layout)
    # Return the Plotly graph object
    return fig


def ProductsPieChart(collection_name):
    database = mongoClient.getDatabase(db_name=db_name)
    # Retrieve ratings data for the given collection
    collection = database[collection_name]
    ratings_data = collection.aggregate([
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}}
    ])

    # Initialize rating labels and counts
    rating_labels = ['1', '2', '3', '4', '5']
    rating_counts = [0, 0, 0, 0, 0]
    for rating in ratings_data:
        rating_labels.append(rating['_id'])
        rating_counts.append(rating['count'])

    # Create a Plotly pie chart
    data = [go.Pie(labels=rating_labels, values=rating_counts)]

    layout = go.Layout(
        title=f"Ratings for {collection_name}"
    )

    fig = go.Figure(data=data, layout=layout)
    # Save the Plotly graph as an HTML file
    graph_html = f"static/{collection_name}.html"
    fig.write_html(graph_html)
    # Return the path to the generated HTML file
    return graph_html


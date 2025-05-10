from flask import Flask, render_template, request, flash
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)
app.secret_key = 'bf603aefb078ed6650460e3f'

data = pd.read_csv("zomato.csv")

class RestaurantForm(FlaskForm):
    location = SelectField('Location', validators=[DataRequired()])
    book_table = SelectField('Book Table', choices=[('Yes', 'Yes'), ('No', 'No')])
    online_order = SelectField('Online Order', choices=[('Yes', 'Yes'), ('No', 'No')])
    rating = FloatField('Rating', validators=[DataRequired()])
    votes = IntegerField('Reviews', validators=[DataRequired()])
    approx_cost = FloatField('Approx Cost', validators=[DataRequired()])
    res_type = SelectField('Type', validators=[DataRequired()])
    submit = SubmitField('Submit')


def recommend(location, data, book_table, online_order, rating, reviews, cost, type):
    if location not in data['location'].values:
        return pd.DataFrame(), False

    data = data[data['location'] == location]
    data = data.drop(['location'], axis=1)
    data = data.drop_duplicates(subset=['name'], keep='first')
    data1 = data.copy()

    if len(data) < 5:
        return data1.reset_index(drop=True), True

    data[['res1', 'res2']] = data['rest_type'].str.split(',', expand=True)
    data['res1'] = data['res1'].fillna('Unknown').astype('category')

    data = data.drop(['name', 'dish_liked', 'cuisines', 'rest_type', 'res2', 'type'], axis=1, errors='ignore')
    data = data.replace(['Yes', 'No'], [1, 0])

    data['approx_cost'] = data['approx_cost'].astype(str).str.replace(',', '', regex=False)
    data['approx_cost'] = pd.to_numeric(data['approx_cost'], errors='coerce').fillna(0)

    data['res1'] = data['res1'].cat.codes

    model = NearestNeighbors(n_neighbors=min(5, len(data)))
    model.fit(data)

    book_table = 1 if book_table == 'Yes' else 0
    online_order = 1 if online_order == 'Yes' else 0

    li = ['Bakery', 'Bar', 'Beverage Shop', 'Cafe', 'Casual Dining', 'Delivery', 'Dessert Parlor', 'Pub', 'Lounge', 'Mess', 'Quick Bites', 'Sweet Shop', 'Takeaway']
    try:
        type_index = li.index(type)
    except ValueError:
        type_index = 0

    user_input = [[book_table, online_order, rating, reviews, cost, type_index]]
    a = model.kneighbors(user_input)

    indices = a[1][0]
    new_df = data1.iloc[indices].reset_index(drop=True)
    return new_df, False


@app.route('/', methods=['GET', 'POST'])
def main():
    form = RestaurantForm()
    form.location.choices = sorted(data['location'].dropna().unique())
    form.res_type.choices = sorted(set(','.join(data['rest_type'].dropna()).split(',')))

    recommended_rest_list = []
    visibility = 'hidden'

    if form.validate_on_submit():
        recommended_rest, is_less_than_5 = recommend(
            location=form.location.data,
            data=data,
            book_table=form.book_table.data,
            online_order=form.online_order.data,
            rating=form.rating.data,
            reviews=form.votes.data,
            cost=form.approx_cost.data,
            type=form.res_type.data
        )

        for i in range(len(recommended_rest)):
            li = recommended_rest.iloc[i, :].values.flatten().tolist()
            recommended_rest_list.append(li)

        visibility = 'visible'

        if is_less_than_5:
            flash(message='Less than 5 restaurants available in this location. Displaying all registered restaurants.', category='warning')

    return render_template('home.html', form=form, list=recommended_rest_list, visibility=visibility)


import os
from django.shortcuts import render, redirect
from nltk import NaiveBayesClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity as weight_calc
from ShopUser.models import ProductsModel
from GuestUser.views import home


def get_vectors(*strs):
    text = [t for t in strs]
    vectorizer = CountVectorizer(text)
    vectorizer.fit(text)
    return vectorizer.transform(text).toarray()


def get_weight(*strs):
    vectors = [t for t in get_vectors(*strs)]
    return weight_calc(vectors)


def word_feats(attributes):
    return dict([(attribute, True) for attribute in attributes])


def training_set(products):
    train_set = []
    for product in products:
        if os.path.exists("media/images/products/" + str(product.id) + ".jpg"):
            if product.pAttributes != " ":
                attributes = []
                for attribute in product.pAttributes.split(" "):
                    attributes.append(attribute)
                features = [(word_feats(attributes), str(product.id))]
                train_set += features
    return train_set


def posterior_dist(products, desc):
    train_set = training_set(products)
    classifier = NaiveBayesClassifier.train(train_set)
    desc = desc.lower()
    if desc != " ":
        attributes = []
        product_set = []
        for attribute in desc.split(" "):
            attributes.append(attribute)
        if attributes:
            features_set = word_feats(attributes)
            labels = classifier.prob_classify(features_set).samples()
            for product in products:
                if product.id in labels:
                    product_set.append(product)
            return product_set
    return products


def calc_weight(request, desc):
    input_img = str(desc).strip().lower()
    input_img = input_img.split(" ")
    products = []
    for product in request.session['products']:
        if os.path.exists("media/images/products/" + str(product.id) + ".jpg"):
            ds_img = str(product.pAttributes).strip().lower()
            ds_img = ds_img.split(" ")
            weight = get_weight(str(input_img), str(ds_img))
            if weight[0][1] >= request.session['weight']:
                flag = True
                for ch in request.session['choice']:
                    if str(product.id) == str(ch):
                        flag = False
                        break
                if flag:
                    products.append(product)
    if products:
        products = posterior_dist(products, desc)
        request.session['weight'] += 0.1
    else:
        request.session['weight'] -= 0.1
    return products


def calc_weight_init(request, desc):
    input_img = str(desc).strip().lower()
    input_img = input_img.split(" ")
    input_img = set(input_img)
    products = []
    for product in ProductsModel.objects.all():
        if os.path.exists("media/images/products/" + str(product.id) + ".jpg"):
            ds_img = str(product.pCategory).strip().lower()
            ds_img = ds_img.split(" ")
            ds_img = set(ds_img).union(set(ds_img))
            weight = len(input_img.intersection(ds_img)) / len(input_img.union(ds_img))
            if weight == 1.0:
                products.append(product)
    return products


def search(request, desc, choice):
    if request.session['weight'] == 0.0:
        products = calc_weight_init(request, desc)
        if products:
            request.session['products'] = products
            request.session['weight'] = 0.7
            return render(request, 'ShopUser/search.html', {'products': request.session['products']})
    else:
        request.session['choice'].append(choice)
        products = calc_weight(request, desc)
        if products:
            return render(request, 'ShopUser/search.html', {'products': products})
        else:
            request.session['choice'] = []
            products = calc_weight(request, desc)
            if products:
                return render(request, 'ShopUser/search.html', {'products': products})
    return redirect(home)


def search_init(request):
    if request.method == "POST":
        input_img = request.POST.get("txtSearch", "")
        request.session['weight'] = 0.0
        request.session['products'] = []
        request.session['choice'] = []
        return redirect(search, desc=input_img, choice=0)
    else:
        return redirect(home)

from django.db import models

# Create your models here.


class ProductsModel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    pCategory = models.TextField()
    pAttributes = models.TextField()

    class Meta:
        db_table = 'tbl_products'

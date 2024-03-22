from django.db import models

# Create your models here.
class BrokerList(models.Model):
    Name  =models.CharField(max_length=200,blank=True, null=True)

    def __str__(self):
        return str(self.Name)

class AngelTable(models.Model):
    UserID = models.CharField(max_length=200)
    Password = models.CharField(max_length=300,default="Password")
    AppID = models.CharField(max_length = 300,blank=True,default = 'rmLd4Q7J4RSi58y')
    APISecret = models.CharField(max_length = 300,blank=True,default = '6SXtlX3u7Ep4LBpBM0MGyh2CHsvEdQ31Mo66PiZsytM6mzdRmphXIcp4W532BuzzOfADE3lkOAX09VV4nOH2cVCsuPuirxZSAovW')
    AccessToken = models.CharField(max_length = 1000,blank=True, null=True)
    RefreshToken = models.CharField(max_length=300, blank=True, null=True)
    FeedToken = models.CharField(max_length=300, blank=True, null=True)
    mpin = models.CharField(max_length = 10,blank=True, null=True)
    Comment = models.CharField(max_length = 300,blank=True)
    Trade = models.BooleanField(default=False)
    webhook_sub = models.CharField(max_length=200,unique=True)
    LastOrderTime = models.DateTimeField(blank=True,null=True)
    LastOrderStatus = models.BooleanField(default=False)
    ErrorMessage = models.CharField(max_length=200,null=True,blank=True)
    Broker = models.ForeignKey(BrokerList,on_delete=models.CASCADE,default="",null=True)
    LastLoginStatus = models.BooleanField(default=False)
    LastLoginTime = models.DateTimeField(null=True,blank=True)
    LastLoginMessage = models.CharField(max_length=200,null=True,blank=True,default="--- Password invalid--- ")
    OpeningBalance = models.CharField(max_length=200,null=True,blank=True,default="Upcoming")
    ClientName = models.CharField(max_length=200,null=True,blank=True,default="Not Available")
    MobileNumber = models.CharField(max_length=200,null=True,blank=True)
    EmailID = models.CharField(max_length=200,null=True,blank=True)
    ChildOrderStatusLast = models.CharField(max_length=50,null=True,blank=True)
    ChildOrderTimeLast = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.UserID
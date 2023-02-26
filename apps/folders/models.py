from django.db import models
from accounts.models import CustomUser


class Folder(models.Model):
    """A folder for categorizing favorites, contacts, notes or other data.

    Attributes:
        id (int): the unique identifier for the folder
        user (int): the user who created and owns the folder
        page (str): the page to which the folder belongs
        name (str): the name or title of the folder
        home_column (int): whether the folder should be displayed on the home page, and
            if so, what rank it should have within its folder
        home_rank (int): whether the folder should be displayed on the home page, and
            if so, what rank it should have within its folder
        selected (int): for tasks folders,
            whether the folder has been selected to be displayed
        active (int): for task folders,
            whether the folder is active for new task entries
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    page = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    home_column = models.IntegerField(blank=True, null=True)
    home_rank = models.IntegerField(blank=True, null=True)
    selected = models.IntegerField(blank=True, null=True)
    active = models.IntegerField(blank=True, null=True)

    fillable = [
        "name",
        "home_column",
        "home_rank",
        "selected",
        "active",
    ]

    def __str__(self):
        return f"{self.name}"

    class Meta:
        db_table = "app_folder"

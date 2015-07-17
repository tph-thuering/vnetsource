########################################################################################################################
# VECNet CI - Prototype
# Date: 05/02/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################

# Create your views here.
from django.http import HttpResponse
from psycopg2._psycopg import ProgrammingError
from data_services.models import DimUser
from django.conf import settings
import psycopg2


def update_names_and_organizations_in_dim_run_table(request):
    dbpassword = settings.APR_VECNET_ORG_PASSWORD
    count = 0
    for user in DimUser.objects.all():
        username = user.username
        # extract data from VecNet user database using SQL queries
        conn = psycopg2.connect("dbname='allocations' user='vecnet' host='apr.vecnet.org' password='%s'" % dbpassword)
        cur = conn.cursor()
        cur.execute("SELECT firstname, lastname, organization FROM vecnetusers WHERE username='%s';" % username)
        try:
            record = cur.fetchone()
            if record == None:
                print "user %s doesn't exist in VecNet user database" % username
            else:
                user.first_name = record[0]
                user.last_name = record[1]
                user.organization = record[2]
                user.save()
                count += 1
        except ProgrammingError:
            print "user %s doesn't exist in VecNet user database" % username
            pass

    return HttpResponse("OK, %s records updated" % count)
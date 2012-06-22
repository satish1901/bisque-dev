Bisque on the Cloud
===================
.. toctree::
   :maxdepth: 2

   release_notes
   advinstall

It is possible to get a new Bisque instance up and running with minimal effort and technical know-how by using Amazon EC2 and Rightscale.

You need to Sign-up for `Amazon Web Services <http://aws.amazon.com>`_ and `Rightscale <https://www.rightscale.com>`_. 

Tutorials
---------

#. `Sign-up for Amazon Web Services <http://support.rightscale.com/03-Tutorials/01-RightScale/3._Upgrade_Your_Account/1.5_Sign-up_for_AWS>`_

#. `Sign-up for a Free RightScale Account <http://support.rightscale.com/03-Tutorials/01-RightScale/1._Signing_Up_for_RightScale/Sign-up_for_a_Free_RightScale_Account>`_

#. `Add AWS Credentials to RightScale <http://support.rightscale.com/03-Tutorials/01-RightScale/3._Upgrade_Your_Account/1.7_Add_AWS_Credentials_to_the_Dashboard>`_

Starting a new Bisque Instance
------------------------------

#. On Rightscale, import the `Bisque Server Template <https://my.rightscale.com/library/server_templates/Bisque-Server-Template/lineage/15175>`_ 

#. You need to create a security group that allows all TCP traffic from any IP on port '27000'. `How to create a security group using Rightscale <http://support.rightscale.com/12-Guides/Dashboard_Users_Guide/Clouds/AWS_Region/EC2_Security_Groups/Actions/Create_a_New_Security_Group>`_ 

#. Configure a new server with the security group created. When the server is launched for the first time, you will be asked to input various variables used for starting a new bisque instance. `How to COnfigure a rightscale server <http://support.rightscale.com/12-Guides/Getting_Started/Story_of_a_RightScale_Server>`_ 


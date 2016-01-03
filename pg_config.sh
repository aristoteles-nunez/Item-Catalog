apt-get -qqy update
apt-get -qqy install postgresql python3-psycopg2
apt-get -qqy install python3-pip

su postgres -c 'createuser -dRS vagrant'
su vagrant -c 'createdb'

vagrantTip="[35m[1mThe shared directory is located at /vagrant\nTo access your shared files: cd /vagrant(B[m"
echo -e $vagrantTip > /etc/motd


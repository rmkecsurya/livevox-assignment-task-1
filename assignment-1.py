import datetime
import boto3
import os

aws_access_key_id = os.environ.get('aws_access_key_id')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')


def get_desired_capacity(asgName):
    asg = boto3.client("autoscaling", region_name='ap-south-1')
    res = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asgName])
    as_groups = res['AutoScalingGroups'][0]
    desired_cnt = as_groups['DesiredCapacity']
    instance_cnt = len(as_groups['Instances'])
    return desired_cnt == instance_cnt


def verify_instance_az(asgName):
    asg = boto3.client("autoscaling",'ap-south-1')
    res = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asgName])
    as_groups = res['AutoScalingGroups'][0]
    list_of_instances = as_groups['Instances']
    # print(list_of_instances)
    dict = {}
    for i in list_of_instances:
        az = i['AvailabilityZone']
        if az not in dict:
            dict[az] = 1
        else:
            return False
    return True


def verify_security_grp(asgName):
    asg = boto3.client("autoscaling",'ap-south-1')
    ec2_client = boto3.client('ec2','ap-south-1')
    res = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asgName])
    asg_details = res['AutoScalingGroups'][0]
    instances = asg_details['Instances']
    security_grps = []
    imgIds = []
    vpcIds = []
    for instance in instances:
        instance_id = instance['InstanceId']
        ec2_res = ec2_client.describe_instances(InstanceIds=[instance_id])
        if 'Reservations' in ec2_res and len(ec2_res['Reservations']) > 0:
            instan = ec2_res['Reservations'][0]['Instances'][0]
            imgIds.append(instan['ImageId'])
            vpcIds.append(instan['VpcId'])
            for sg in instan['SecurityGroups']:
                security_grps.append(sg['GroupId'])
    if len(set(security_grps)) > 1:
        return False
    if len(set(imgIds)) > 1:
        return False
    if len(set(vpcIds)) > 1:
        return False
    return True


def longest_running_instance(asgName, region):
    ec2_client = boto3.client('ec2', 'ap-south-1')
    asg_client = boto3.client('autoscaling','ap-south-1')
    asg_response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asgName])
    instance_list = asg_response['AutoScalingGroups'][0]['Instances']
    long_time = None
    long_instance = ''
    for instance in instance_list:
        instance_id = instance['InstanceId']
        instance_response = ec2_client.describe_instances(InstanceIds=[instance_id])
        #print(instance_response)
        launch_time = instance_response['Reservations'][0]['Instances'][0]['LaunchTime']
        current_time = datetime.datetime.now(datetime.timezone.utc)
        uptime = current_time - launch_time
        #print(launch_time,current_time,uptime,sep="\n")
        if long_time is None or uptime > long_time:
            long_instance = instance_id
            long_time = uptime
    print(r"Longest running instance is {0} and running time is {1}".format(long_instance,long_time))

auto_scaling_grp_name = 'lv-test-cpu'
region = 'ap-south-1'
if get_desired_capacity(auto_scaling_grp_name):
    print("Desired Instances are running")
else:
    print("Desired instances are not running")

if verify_security_grp(auto_scaling_grp_name):
    print("All the instances has the same Security Group")
else:
    print("Doesn't having the same Security Group")

if verify_instance_az(auto_scaling_grp_name):
    print("Instances are having in different Az's")
else:
    print("Instances aren't in different AZ's")

longest_running_instance(auto_scaling_grp_name,region)

data "openstack_networking_network_v2" "sharednet1" {
  name = "sharednet1"
}

data "openstack_networking_subnet_v2" "sharednet1_subnet" {
  name = "sharednet1-subnet"
}

data "openstack_networking_secgroup_v2" "allow_ssh" {
  name = "allow-ssh"
}

data "openstack_networking_secgroup_v2" "allow_9001" {
  name = "allow-9001"
}

data "openstack_networking_secgroup_v2" "allow_8000" {
  name = "allow-8000"
}

data "openstack_networking_secgroup_v2" "allow_8080" {
  name = "allow-8080"
}

data "openstack_networking_secgroup_v2" "allow_8081" {
  name = "allow-8081"
}

data "openstack_networking_secgroup_v2" "allow_8082" {
  name = "allow-8082"
}

data "openstack_networking_secgroup_v2" "allow_http_80" {
  name = "allow-http-80"
}

data "openstack_networking_secgroup_v2" "allow_9090" {
  name = "allow-9090"
}

data "openstack_networking_secgroup_v2" "immich_nodeport" {
  name = "immich-nodeport-proj21"
}

resource "openstack_networking_secgroup_v2" "adminer_nodeport" {
  name        = "adminer-nodeport-${var.suffix}"
  description = "Allow access to Adminer on NodePort 32082"
}

resource "openstack_networking_secgroup_rule_v2" "adminer_nodeport_rule" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 32082
  port_range_max    = 32082
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.adminer_nodeport.id
}


#!/bin/sh

# this service is required because docker will start only after cloud init was finished
# due to the service dependencies in Fedora Atomic (docker <- docker-storage-setup <- cloud-final)


. /etc/sysconfig/heat-params

KUBE_DNS_RC=/srv/kubernetes/manifests/kube-skydns-rc.yaml
[ -f ${KUBE_DNS_RC} ] || {
    echo "Writing File: $KUBE_DNS_RC"
    mkdir -p $(dirname ${KUBE_DNS_RC})
    cat << EOF > ${KUBE_DNS_RC}
apiVersion: v1
kind: ReplicationController
metadata:
  name: kube-dns-v11
  namespace: kube-system
  labels:
    k8s-app: kube-dns
    version: v11
    kubernetes.io/cluster-service: "true"
spec:
  replicas: 1
  selector:
    k8s-app: kube-dns
    version: v11
  template:
    metadata:
      labels:
        k8s-app: kube-dns
        version: v11
        kubernetes.io/cluster-service: "true"
    spec:
      containers:
      - name: etcd
        image: gcr.io/google_containers/etcd-amd64:2.2.1
        resources:
          # TODO: Set memory limits when we've profiled the container for large
          # clusters, then set request = limit to keep this container in
          # guaranteed class. Currently, this container falls into the
          # "burstable" category so the kubelet doesn't backoff from restarting it.
          limits:
            cpu: 100m
            memory: 500Mi
          requests:
            cpu: 100m
            memory: 50Mi
        command:
        - /usr/local/bin/etcd
        - -data-dir
        - /var/etcd/data
        - -listen-client-urls
        - http://127.0.0.1:2379,http://127.0.0.1:4001
        - -advertise-client-urls
        - http://127.0.0.1:2379,http://127.0.0.1:4001
        - -initial-cluster-token
        - skydns-etcd
        volumeMounts:
        - name: etcd-storage
          mountPath: /var/etcd/data
      - name: kube2sky
        image: gcr.io/google_containers/kube2sky:1.14
        resources:
          # TODO: Set memory limits when we've profiled the container for large
          # clusters, then set request = limit to keep this container in
          # guaranteed class. Currently, this container falls into the
          # "burstable" category so the kubelet doesn't backoff from restarting it.
          limits:
            cpu: 100m
            # Kube2sky watches all pods.
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 50Mi
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8081
            scheme: HTTP
          # we poll on pod startup for the Kubernetes master service and
          # only setup the /readiness HTTP server once that's available.
          initialDelaySeconds: 30
          timeoutSeconds: 5
        args:
        # command = "/kube2sky"
        - --domain=cluster.local
        - --kubecfg-file=/srv/kubernetes/kubeconfig.yaml
        volumeMounts:
        - mountPath: /srv/kubernetes/
          name: config-vol
      - name: skydns
        image: gcr.io/google_containers/skydns:2015-10-13-8c72f8c
        resources:
          # TODO: Set memory limits when we've profiled the container for large
          # clusters, then set request = limit to keep this container in
          # guaranteed class. Currently, this container falls into the
          # "burstable" category so the kubelet doesn't backoff from restarting it.
          limits:
            cpu: 100m
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 50Mi
        args:
        # command = "/skydns"
        - -machines=http://127.0.0.1:4001
        - -addr=0.0.0.0:53
        - -ns-rotate=false
        - -domain=cluster.local.
        ports:
        - containerPort: 53
          name: dns
          protocol: UDP
        - containerPort: 53
          name: dns-tcp
          protocol: TCP
      - name: healthz
        image: gcr.io/google_containers/exechealthz:1.0
        resources:
          # keep request = limit to keep this container in guaranteed class
          limits:
            cpu: 10m
            memory: 20Mi
          requests:
            cpu: 10m
            memory: 20Mi
        args:
        - -cmd=nslookup kubernetes.default.svc.cluster.local 127.0.0.1 >/dev/null
        - -port=8080
        ports:
        - containerPort: 8080
          protocol: TCP
      volumes:
      - name: etcd-storage
        emptyDir: {}
      - name: config-vol
        hostPath:
          path: /srv/kubernetes/
      dnsPolicy: Default  # Don't use cluster DNS.
EOF
}

KUBE_DNS_SVC=/srv/kubernetes/manifests/kube-skydns-svc.yaml
[ -f ${KUBE_DNS_SVC} ] || {
    echo "Writing File: $KUBE_DNS_SVC"
    mkdir -p $(dirname ${KUBE_DNS_SVC})
    cat << EOF > ${KUBE_DNS_SVC}
apiVersion: v1
kind: Service
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    k8s-app: kube-dns
    kubernetes.io/cluster-service: "true"
    kubernetes.io/name: "KubeDNS"
spec:
  selector:
    k8s-app: kube-dns
  clusterIP:  10.254.10.10
  ports:
  - name: dns
    port: 53
    protocol: UDP
  - name: dns-tcp
    port: 53
    protocol: TCP
EOF
}

KUBE_DNS_BIN=/usr/local/bin/kube-dns
[ -f ${KUBE_DNS_BIN} ] || {
    echo "Writing File: $KUBE_DNS_BIN"
    mkdir -p $(dirname ${KUBE_DNS_BIN})
    cat << EOF > ${KUBE_DNS_BIN}
#!/bin/sh
until curl -sf "http://127.0.0.1:8080/healthz"
do
    echo "Waiting for Kubernetes API..."
    sleep 5
done

/usr/bin/kubectl create -f $KUBE_DNS_RC --namespace=kube-system
/usr/bin/kubectl create -f $KUBE_DNS_SVC --namespace=kube-system
EOF
}

KUBE_DNS_SERVICE=/etc/systemd/system/kube-dns.service
[ -f ${KUBE_DNS_SERVICE} ] || {
    echo "Writing File: $KUBE_DNS_SERVICE"
    mkdir -p $(dirname ${KUBE_DNS_SERVICE})
    cat << EOF > ${KUBE_DNS_SERVICE}
[Unit]
After=kube-apiserver.service
Requires=kube-apiserver.service

[Service]
Type=oneshot
Environment=HOME=/root
EnvironmentFile=-/etc/kubernetes/config
ExecStart=${KUBE_DNS_BIN}

[Install]
WantedBy=multi-user.target
EOF
}

chown root:root ${KUBE_DNS_BIN}
chmod 0755 ${KUBE_DNS_BIN}

chown root:root ${KUBE_DNS_SERVICE}
chmod 0644 ${KUBE_DNS_SERVICE}

systemctl enable kube-dns
systemctl start --no-block kube-dns

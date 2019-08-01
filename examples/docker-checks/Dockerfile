FROM minitor-dev-linux-amd64

RUN apk add bash jq curl

RUN addgroup -S minitor && adduser -S minitor -G minitor

USER minitor

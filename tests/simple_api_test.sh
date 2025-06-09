# Generate traffic using valid endpoints
for i in {1..20}; do
  curl http://localhost:8000/health
  sleep 1
  curl http://localhost:8000/model/info
  sleep 1
done

# for i in {1..20}; do
#   curl http://localhost:8000/api/v1/models
#   sleep 1
# done

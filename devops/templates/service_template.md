# Service Template (BAL/BLL/DAL)
- `bal/`: HTTP layer and serializers.
- `bll/`: business rules and orchestration.
- `dal/`: data access only.
- Must emit events via Redis bus.
- Must append audit records for critical state changes.

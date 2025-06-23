# Pan-SCM-SDK Insights API Requirements

## Overview

The pan-scm-cli project needs insights and monitoring capabilities to be added to the pan-scm-sdk. This document outlines the required SDK services, methods, and data structures needed to support the SCM insights functionality.

## Background

Based on research of the Strata Cloud Manager APIs, there are several monitoring and insights services available:
- Strata Insights
- Aggregate Monitoring
- Multitenant Notifications
- Autonomous DEM (Digital Experience Monitoring)

These services provide telemetry, notification, and performance monitoring capabilities that go beyond configuration management.

## Required SDK Services

### 1. Alerts Service (`scm.client.alerts`)

**Methods needed:**
- `list(**kwargs)` - List alerts with filtering capabilities
- `get(alert_id: str, **kwargs)` - Get a specific alert by ID

**Supported filters:**
- `folder` - Filter by folder
- `severity` - Filter by severity level (critical, high, medium, low)
- `start_time` - Filter alerts from this timestamp
- `end_time` - Filter alerts up to this timestamp
- `status` - Filter by alert status (active, resolved, acknowledged)
- `category` - Filter by alert category
- `max_results` - Limit number of results

**Data structure:**
```python
class Alert:
    id: str
    name: str
    severity: str  # critical, high, medium, low
    status: str
    timestamp: str  # ISO format
    description: Optional[str]
    folder: Optional[str]
    source: Optional[str]
    category: Optional[str]
    impacted_resources: List[str]
    metadata: Dict[str, Any]
```

### 2. Mobile Users Service (`scm.client.mobile_users`)

**Methods needed:**
- `list(**kwargs)` - List mobile users with filtering
- `get(user_id: str, **kwargs)` - Get specific mobile user

**Supported filters:**
- `folder` - Filter by folder
- `status` - Filter by connection status (connected, disconnected)
- `location` - Filter by location
- `gateway` - Filter by gateway
- `max_results` - Limit number of results

**Data structure:**
```python
class MobileUser:
    id: str
    username: str
    device_id: Optional[str]
    status: str  # connected, disconnected
    location: Optional[str]
    last_seen: Optional[str]  # ISO format
    ip_address: Optional[str]
    folder: Optional[str]
    gateway: Optional[str]
    bandwidth_used: Optional[int]  # in Mbps
    session_duration: Optional[int]  # in seconds
    metadata: Dict[str, Any]
```

### 3. Locations Service (`scm.client.locations`)

**Methods needed:**
- `list(**kwargs)` - List locations with filtering
- `get(location_id: str, **kwargs)` - Get specific location

**Supported filters:**
- `folder` - Filter by folder
- `region` - Filter by geographic region
- `country` - Filter by country
- `max_results` - Limit number of results

**Data structure:**
```python
class Location:
    id: str
    name: str
    region: Optional[str]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    folder: Optional[str]
    total_users: Optional[int]
    active_users: Optional[int]
    bandwidth_capacity: Optional[int]  # in Mbps
    bandwidth_used: Optional[int]  # in Mbps
    metadata: Dict[str, Any]
```

### 4. Remote Network Insights Service (`scm.client.remote_network_insights`)

**Methods needed:**
- `list(**kwargs)` - List remote network insights
- `get(network_id: str, **kwargs)` - Get specific network insights

**Supported filters:**
- `folder` - Filter by folder
- `connectivity_status` - Filter by status (connected, disconnected, degraded)
- `region` - Filter by region
- `include_metrics` - Include performance metrics
- `max_results` - Limit number of results

**Data structure:**
```python
class RemoteNetworkInsights:
    id: str
    name: str
    connectivity_status: str  # connected, disconnected, degraded
    folder: Optional[str]
    site_id: Optional[str]
    region: Optional[str]
    bandwidth_allocated: Optional[int]  # in Mbps
    bandwidth_used: Optional[int]  # in Mbps
    latency: Optional[float]  # in milliseconds
    packet_loss: Optional[float]  # percentage
    jitter: Optional[float]  # in milliseconds
    tunnel_count: Optional[int]
    active_tunnels: Optional[int]
    last_status_change: Optional[str]  # ISO format
    metadata: Dict[str, Any]
```

### 5. Service Connection Insights Service (`scm.client.service_connection_insights`)

**Methods needed:**
- `list(**kwargs)` - List service connection insights
- `get(connection_id: str, **kwargs)` - Get specific connection insights

**Supported filters:**
- `folder` - Filter by folder
- `health_status` - Filter by health (healthy, unhealthy, degraded)
- `service_type` - Filter by service type (aws, azure, gcp, etc.)
- `include_metrics` - Include performance metrics
- `max_results` - Limit number of results

**Data structure:**
```python
class ServiceConnectionInsights:
    id: str
    name: str
    health_status: str  # healthy, unhealthy, degraded
    folder: Optional[str]
    region: Optional[str]
    service_type: Optional[str]
    latency: Optional[float]  # in milliseconds
    throughput: Optional[float]  # in Mbps
    availability: Optional[float]  # percentage
    uptime: Optional[int]  # in seconds
    last_health_check: Optional[str]  # ISO format
    error_count: Optional[int]
    warning_count: Optional[int]
    metadata: Dict[str, Any]
```

### 6. Tunnels Service (`scm.client.tunnels`)

**Methods needed:**
- `list(**kwargs)` - List tunnels with filtering
- `get(tunnel_id: str, **kwargs)` - Get specific tunnel

**Supported filters:**
- `folder` - Filter by folder
- `status` - Filter by status (up, down)
- `tunnel_type` - Filter by type (IPSec, SSL, etc.)
- `include_stats` - Include performance statistics
- `start_time` - For historical data
- `end_time` - For historical data
- `max_results` - Limit number of results

**Data structure:**
```python
class Tunnel:
    id: str
    name: str
    status: str  # up, down
    tunnel_type: Optional[str]  # IPSec, SSL, etc.
    folder: Optional[str]
    source_zone: Optional[str]
    destination_zone: Optional[str]
    local_address: Optional[str]
    remote_address: Optional[str]
    bytes_sent: Optional[int]
    bytes_received: Optional[int]
    packets_sent: Optional[int]
    packets_received: Optional[int]
    latency: Optional[float]  # in milliseconds
    jitter: Optional[float]  # in milliseconds
    packet_loss: Optional[float]  # percentage
    uptime: Optional[int]  # in seconds
    last_state_change: Optional[str]  # ISO format
    metadata: Dict[str, Any]
```

## API Endpoints

Based on the SCM API documentation research, these services should integrate with the following API endpoints:

### Aggregate Monitoring API
- Base URL: `https://api.strata.paloaltonetworks.com/mt/monitor/v1/agg/`
- Requires `x-panw-region` header
- Uses OAuth 2.0 authentication

### Example Endpoints
- Alerts: `/mt/monitor/v1/agg/alerts/list?agg_by=tenant`
- Mobile Users: `/sse/monitor/v1/mobile-users`
- Locations: `/sse/monitor/v1/locations`
- Remote Networks: `/sse/monitor/v1/remote-networks/insights`
- Service Connections: `/sse/monitor/v1/service-connections/insights`
- Tunnels: `/sse/monitor/v1/tunnels`

## Implementation Notes

1. **Authentication**: All endpoints use the existing OAuth 2.0 authentication mechanism already implemented in pan-scm-sdk.

2. **Region Header**: Some monitoring APIs require the `x-panw-region` header. This should be configurable or auto-detected based on the TSG configuration.

3. **Pagination**: All list methods should support pagination with `offset` and `limit` parameters.

4. **Error Handling**: The SDK should handle common monitoring API errors:
   - 404: Resource not found
   - 403: Insufficient permissions for monitoring data
   - 429: Rate limiting
   - 503: Monitoring service temporarily unavailable

5. **Mock Support**: The SDK should provide mock data for testing when the client is initialized without valid credentials (similar to existing configuration services).

6. **Real-time Support**: Consider future support for WebSocket connections or long-polling for real-time alert monitoring.

## Benefits

Implementing these insights services in the SDK will enable:
- Real-time monitoring of network health and performance
- Proactive alerting and issue detection
- Historical analysis of network metrics
- Capacity planning based on usage trends
- Compliance reporting with activity tracking
- Integration with external monitoring systems

## Priority

Suggested implementation priority:
1. **High Priority**: Alerts, Tunnels (core monitoring functionality)
2. **Medium Priority**: Mobile Users, Remote Network Insights, Service Connection Insights
3. **Lower Priority**: Locations (mostly static data)

## Testing Requirements

Each service should include:
- Unit tests with mock data
- Integration tests against test SCM environments
- Performance tests for large datasets
- Mock mode support for CLI testing
# API Documentation

The purpose of this guide is to offer insights into the various endpoints, request and response formats, authentication methods, and more. We encourage collaboration and value your feedback, so if you encounter a missing feature or have an idea for improvement, don't hesitate to create an issue. Oftentimes, seemingly complex functionalities can be straightforward to implement, and your input helps us enhance the API for everyone.

## Table of Contents

* [API Endpoint `/api/blocks`](#api-endpoint---api-blocks-)
* [API Endpoint `/api/epochs`](#api-endpoint---api-epochs-)
* [API Endpoint `/api/attestations`](#api-endpoint---api-attestations-)
* [API Endpoint `/api/attestations_for_slots`](#api-endpoint---api-attestations-for-slots-)
* [API Endpoint `/api/withdrawals`](#api-endpoint---api-withdrawals-)
* [API Endpoint `/api/sync_committee_participation`](#api-endpoint--api-sync-committee-participation-)
* [API Endpoint `/api/rewards_and_penalties`](#api-endpoint---api-rewards-and-penalties-)
* [API Endpoint `/api/chart_data`](#api-endpoint---api-chart-data-)
* [API Endpoint `/api/validators`](#api-endpoint---api-validators-)
* [API Endpoint `/api/check_if_proposal_scheduled`](#api-endpoint---api-check-if-proposal-scheduled-)
* [API Endpoint `/api/blocks_by_proposer`](#api-endpoint---api-blocks-by-proposer-)
* [API Endpoint `/api/current_beacon_state`](#api-endpoint---api-current-beacon-state-)
* [API Endpoint `/api/validators_by_id`](#api-endpoint---api-validators-by-id-)

## API Endpoint `/api/blocks`

### Description
The `/api/blocks` API function allows you to retrieve a list of blocks based on certain parameters.

### Parameters
1. `range` (optional, default: 10)
The number of blocks to retrieve from the starting point. It must be an integer between 1 and 100 (inclusive). If not provided, the default value is 10.

2. `direction` (optional, default: "descending")
The direction in which blocks will be retrieved. It can have two values:
- `ascending`: Blocks will be retrieved in ascending order based on their slot numbers.
- `descending`: Blocks will be retrieved in descending order based on their slot numbers.

3. `from_slot` (required)
The starting point for block retrieval. It can take two types of values:
- Integer value: A specific slot number to start retrieval from.
- String value `head`: The retrieval will start from the latest block's slot number.

4. `omit_pending` (optional, default: False)
A boolean flag to exclude pending blocks (blocks with empty flag equal to 3) from the retrieved list. By default, pending blocks are included.

### Response
The API returns a JSON response with the following structure:
```yaml
{
    "success": true,                   // Indicates whether the API call was successful or not
    "from_slot": <from_slot>,          // The provided from_slot or in the case of head the actually used slot
    "range": <range_value>,            // The provided range
    "direction": <direction_value>,    // The provided direction
    "data": [                          // An array containing the retrieved block data
        {
            "proposer": <address>,     // Address of the block proposer
            "block_number": <int>,     // Block number
            "slot_number": <int>,      // Slot number of the block
            "fee_recipient": <address>,// Address of the fee recipient
            "timestamp": <datetime>,   // Timestamp of the block in ISO 8601 format
            "total_reward": <float>,   // Total (execution) reward (converted to float)
            "epoch": <int>,            // Epoch number of the block
            "empty": <int>             // Empty flag (0 if not processed yet, 1 if not empty/not proposed, 2 if orphaned, 3 if pending)
        },
        // More block entries
    ]
}
```

### Example
#### Request
```
GET /api/blocks/?range=5&direction=descending&from_slot=7000000&omit_pending=true
```

#### Response
```json
{"success": true, "data": [{"proposer": 210833, "block_number": 17814442, "slot_number": 7000000, "fee_recipient": "0x690b9a9e9aa1c9db991c7721a92d351db4fac990", "timestamp": "2023-07-31T17:20:23+00:00", "total_reward": 0.06167452201140929, "epoch": 218750, "empty": 0}, {"proposer": 613138, "block_number": 17814441, "slot_number": 6999999, "fee_recipient": "0xbd3afb0bb76683ecb4225f9dbc91f998713c3b01", "timestamp": "2023-07-31T17:20:11+00:00", "total_reward": 0.03767648283640269, "epoch": 218749, "empty": 0}, {"proposer": 157428, "block_number": 17814440, "slot_number": 6999998, "fee_recipient": "0xdafea492d9c6733ae3d56b7ed1adb60692c98bc5", "timestamp": "2023-07-31T17:19:59+00:00", "total_reward": 0.10128858669822016, "epoch": 218749, "empty": 0}, {"proposer": 528504, "block_number": 17814439, "slot_number": 6999997, "fee_recipient": "0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5", "timestamp": "2023-07-31T17:19:47+00:00", "total_reward": 0.059309297352723986, "epoch": 218749, "empty": 0}, {"proposer": 507796, "block_number": 17814438, "slot_number": 6999996, "fee_recipient": "0xdafea492d9c6733ae3d56b7ed1adb60692c98bc5", "timestamp": "2023-07-31T17:19:35+00:00", "total_reward": 0.06787533680208976, "epoch": 218749, "empty": 0}], "from_slot": 7000000, "range": 5, "direction": "descending"}
```

### Notes
- The timestamp is provided in ISO 8601 format for easy parsing and consistency.
- The total_reward is converted to a float value for better readability (converted from the original wei unit).

## API Endpoint `/api/epochs`

### Description

The `/api/epochs` API function allows you to retrieve a list of epochs along with various statistics related to each epoch. An epoch is a fixed period in a blockchain network during which a fixed number of slots are produced.

### Parameters

1. `range` (optional, default: 10)
The number of epochs to retrieve from the starting point. It must be an integer between 1 and 100 (inclusive). If not provided, the default value is 10.

2. `direction` (optional, default: "descending")
The direction in which epochs will be retrieved. It can have two values:
- ascending: Epochs will be retrieved in ascending order based on their epoch numbers.
- descending: Epochs will be retrieved in descending order based on their epoch numbers.

3. `from_epoch` (required)
The starting point for epoch retrieval. It can take two types of values:
- Integer value: A specific epoch number to start retrieval from.
- String value `head`: The retrieval will start from the latest epoch's number.

### Response
The API returns a JSON response with the following structure:
```yaml
{
    "success": true,                          // Indicates whether the API call was successful or not
    "from_slot": <from_slot>,                 // The provided from_slot or in the case of head the actually used slot
    "range": <range_value>,                   // The provided range
    "direction": <direction_value>,           // The provided direction
    "data": [                                 // An array containing the retrieved epoch data
        {
            "epoch": <int>,                   // Epoch number
            "timestamp": <datetime>,          // Timestamp of the epoch in ISO 8601 format
            "missed_attestation_count": <int>, // Number of missed attestations in the epoch
            "total_attestations": <int>,      // Total number of attestations in the epoch
            "participation_percent": <float>, // Participation percentage in the epoch (in decimals)
            "epoch_total_proposed_blocks": <int>,    // Total number of blocks proposed in the epoch
            "average_block_reward": <float>,   // Average block reward in ETH (converted to float)
            "highest_block_reward": <float>    // Highest block reward in ETH (converted to float)
        },
        // More epoch entries
    ]
}
```

### Example

#### Request
```
GET /api/epochs/?range=5&direction=descending&from_epoch=200000
```

#### Response
```json
{"success": true, "data": [{"epoch": 200000, "timestamp": "2023-05-09T09:20:23+00:00", "missed_attestation_count": 2462, "total_attestations": 563000, "participation_percent": 99.56269982238011, "epoch_total_proposed_blocks": 30, "average_block_reward": 0.15004758197114265, "highest_block_reward": 0.6419720456289241}, {"epoch": 199999, "timestamp": "2023-05-09T09:13:59+00:00", "missed_attestation_count": 2062, "total_attestations": 562992, "participation_percent": 99.63374257538295, "epoch_total_proposed_blocks": 32, "average_block_reward": 0.14922107416212663, "highest_block_reward": 1.406198503439747}, {"epoch": 199998, "timestamp": "2023-05-09T09:07:35+00:00", "missed_attestation_count": 1804, "total_attestations": 562985, "participation_percent": 99.67956517491585, "epoch_total_proposed_blocks": 32, "average_block_reward": 0.12165577341174186, "highest_block_reward": 0.34745862172664244}, {"epoch": 199997, "timestamp": "2023-05-09T09:01:11+00:00", "missed_attestation_count": 1854, "total_attestations": 562979, "participation_percent": 99.67068043390606, "epoch_total_proposed_blocks": 32, "average_block_reward": 0.16928325925557214, "highest_block_reward": 0.9558263427967987}, {"epoch": 199996, "timestamp": "2023-05-09T08:54:47+00:00", "missed_attestation_count": 1715, "total_attestations": 562979, "participation_percent": 99.69537052003716, "epoch_total_proposed_blocks": 32, "average_block_reward": 0.09695609574259342, "highest_block_reward": 0.4847419977156581}], "from_epoch": 200000, "range": 5, "direction": "descending"}
```

### Notes
- The timestamp is provided in ISO 8601 format for easy parsing and consistency.
- The average_block_reward and highest_block_reward are converted to float values for better readability (converted from the original token unit).
- The participation_percent is calculated dynamically based on the number of missed attestations and total attestations if not provided explicitly in the database.





## API Endpoint `/api/attestations`

### Description
The `/api/attestations` API function allows you to retrieve attestation data for a given set of validators within a specified range of slots. Attestations are votes cast by validators to validate and propose blocks in a blockchain network.

### Parameters
1. `validators` (required)
A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `from_slot` (required)
The starting slot number for attestation retrieval. It must be an integer value.

3. `to_slot` (optional)
The ending slot number for attestation retrieval. It must be an integer value. If not provided, the retrieval will go up to the latest available slot.

4. `include_pending` (optional, default: "auto")
A boolean flag to include pending attestations in the retrieval. It can have three values:
- `auto` (default): The API will automatically decide whether to include pending attestations based on the number of validator IDs. If there are more than 10 validator IDs, pending attestations will be excluded; otherwise, they will be included.
- `True`: Include pending attestations.
- `False`: Exclude pending attestations.

### Response
The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                     // Indicates whether the API call was successful or not
    "from_slot": <int>,                  // The starting slot number used for retrieval
    "to_slot": <int>                     // The ending slot number used for retrieval
    "data": [                            // An array containing the retrieved attestation data
        {
            "validator_id": <int>,       // Validator ID
            "slot_number": <int>,        // Slot number of the attestation
            "distance": <int>,           // Distance of the attestation
            "epoch": <int>,              // Epoch number of the attestation
            "block_timestamp": <datetime>, // Timestamp of the corresponding block in ISO 8601 format
        },
        // More attestation entries
    ],
}
```

### Example

#### Request

```
GET /api/attestations/?validators=1,2,3,4,5,6,7,8,9,10,11,12&from_slot=7000000&to_slot=7000010&include_pending=false
```

#### Response

```json
{"success": true, "data": [{"epoch": 218750, "distance": 0, "slot": 7000006, "block_timestamp": "2023-07-31T17:21:47+00:00", "validator_id": 6}, {"epoch": 218750, "distance": 0, "slot": 7000006, "block_timestamp": "2023-07-31T17:21:47+00:00", "validator_id": 8}, {"epoch": 218750, "distance": 0, "slot": 7000003, "block_timestamp": "2023-07-31T17:21:11+00:00", "validator_id": 9}, {"epoch": 218750, "distance": 0, "slot": 7000002, "block_timestamp": "2023-07-31T17:20:59+00:00", "validator_id": 10}], "from_slot": 7000000, "to_slot": 7000010}
```

### Notes
- The block_timestamp field indicates the timestamp of the corresponding block in the blockchain for each attestation.


## API Endpoint `/api/attestations_for_slots`

### Description
The `/api/attestations_for_slots` API function allows you to retrieve attestation data for a given set of validators within a specified range of slots. It differs from /api/attestations by providing attestation data for individual slots and includes the attestation distance values as an array for each validator ID that attestet during the specified slots. Therefore it is more suitable for a huge validator set.

### Parameters
1. `validators` (required)
A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `from_slot` (required)
The starting slot number for attestation retrieval. It must be an integer value.

3. `to_slot` (optional)
The ending slot number for attestation retrieval. It must be an integer value. If not provided, the retrieval will go up to the latest available slot.

4. `range` (optional, default: 10)
The number of slots to retrieve attestation data from the starting slot. It must be an integer between 1 and 10 (inclusive). If not provided, the default value is 10.

5. `include_pending` (optional, default: False)
A boolean flag to include pending attestations in the retrieval.

### Response
The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                       // Indicates whether the API call was successful or not
    "from_slot": <int>,                    // The starting slot number used for retrieval
    "to_slot": <int>                       // The ending slot number used for retrieval
    "data": [                              // An array containing the retrieved attestation data
        {
            "validator_id": <list>,        // Validator IDs
            "slot_number": <int>,          // Slot number of the attestation
            "distance": <list>,            // List of distances for the attestation
            "epoch": <int>,                // Epoch number of the attestation
            "block_timestamp": <datetime>, // Timestamp of the corresponding block in ISO 8601 format
        },
        // More attestation entries
    ],
}
```

### Notes
- The block_timestamp field indicates the timestamp of the corresponding block in the blockchain for each attestation.
- The distance field contains a list of distances for the given validator IDs in each slot.

### Example

#### Request

```
GET /api/attestations_for_slots/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50&from_slot=7000001&to_slot=7000010&include_pending=false
```

#### Response

```json
{"success": true, "data": [{"epoch": 218750, "distance": [], "slot": 7000010, "block_timestamp": "2023-07-31T17:22:35+00:00", "validator_id": []}, {"epoch": 218750, "distance": [0], "slot": 7000009, "block_timestamp": "2023-07-31T17:22:23+00:00", "validator_id": [18]}, {"epoch": 218750, "distance": [], "slot": 7000008, "block_timestamp": "2023-07-31T17:22:11+00:00", "validator_id": []}, {"epoch": 218750, "distance": [0], "slot": 7000007, "block_timestamp": "2023-07-31T17:21:59+00:00", "validator_id": [14]}, {"epoch": 218750, "distance": [0, 0, 0, 0], "slot": 7000006, "block_timestamp": "2023-07-31T17:21:47+00:00", "validator_id": [6, 8, 27, 20]}, {"epoch": 218750, "distance": [0], "slot": 7000005, "block_timestamp": "2023-07-31T17:21:35+00:00", "validator_id": [49]}, {"epoch": 218750, "distance": [0, 0], "slot": 7000004, "block_timestamp": "2023-07-31T17:21:23+00:00", "validator_id": [15, 17]}, {"epoch": 218750, "distance": [0, 0], "slot": 7000003, "block_timestamp": "2023-07-31T17:21:11+00:00", "validator_id": [21, 9]}, {"epoch": 218750, "distance": [0, 0], "slot": 7000002, "block_timestamp": "2023-07-31T17:20:59+00:00", "validator_id": [50, 10]}, {"epoch": 218750, "distance": [0, 0], "slot": 7000001, "block_timestamp": "2023-07-31T17:20:47+00:00", "validator_id": [47, 13]}], "from_slot": 7000001, "to_slot": 7000010}
```

## API Endpoint `/api/withdrawals`

### Description

The `/api/withdrawals` API function enables you to retrieve withdrawal data for a given set of validators.

### Parameters


1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `range` (optional, default: 10)

The number of withdrawal records to retrieve. It must be an integer between 1 and 100 (inclusive). If not provided, the default value is 10.

3. `cursor` (optional, default: 0)

A numeric value indicating the starting position for withdrawal retrieval. It represents the index of the first record to fetch (newest to oldest). If not provided, the default value is 0.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                     // Indicates whether the API call was successful or not
    "data": [                            // An array containing the retrieved withdrawal data
        {
            "validator_id": <int>,       // Validator ID
            "address": <string>,         // Address to which funds were withdrawn
            "amount": <float>,           // Withdrawal amount in ETH (converted to float)
            "slot_number": <int>,        // Slot number of the block containing the withdrawal
            "timestamp": <datetime>,     // Timestamp of the withdrawal in ISO 8601 format
        },
        // More withdrawal entries
    ],
    "range_value": <int>,                // The provided range value
    "cursor_value": <int>                // The provided cursor value
}
```

## Examples

### Request

```
GET /api/withdrawals/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14&range=5&cursor=0
```

### Response

```json
{"success": true, "data": [{"validator": 4, "address": "0x15f4b914a0ccd14333d850ff311d6dafbfbaa32b", "amount": 0.014990772, "block__slot_number": 7019528, "block__timestamp": "2023-08-03T10:25:59+00:00"}, {"validator": 3, "address": "0x15f4b914a0ccd14333d850ff311d6dafbfbaa32b", "amount": 0.015053007, "block__slot_number": 7019528, "block__timestamp": "2023-08-03T10:25:59+00:00"}, {"validator": 2, "address": "0x15f4b914a0ccd14333d850ff311d6dafbfbaa32b", "amount": 0.015030387, "block__slot_number": 7019528, "block__timestamp": "2023-08-03T10:25:59+00:00"}, {"validator": 1, "address": "0x15f4b914a0ccd14333d850ff311d6dafbfbaa32b", "amount": 0.015055973, "block__slot_number": 7019528, "block__timestamp": "2023-08-03T10:25:59+00:00"}, {"validator": 4, "address": "0x15f4b914a0ccd14333d850ff311d6dafbfbaa32b", "amount": 0.014258164, "block__slot_number": 6977122, "block__timestamp": "2023-07-28T13:04:47+00:00"}], "range_value": 5, "cursor_value": 0}
```

## API Endpoint`/api/sync_committee_participation`

### Description

The `/api/sync_committee_participation` API function allows you to retrieve participation data of validators in the sync committee for a specified range of slots. This API provides insights into validator contributions during sync committee periods.

### Parameters


1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `range` (optional, default: 10)

The number of sync committee participation records to retrieve. It must be an integer between 1 and 100 (inclusive). If not provided, the default value is 10. Only limits the number of returned entries not the slot range.

3. `from_slot` (required)

The starting slot number for sync committee participation retrieval. It must be an integer value. Returns the first sync committee duties before the `from_slot`.

4. `include_pending` (optional, default: False)

A boolean flag to include pending sync committee duties.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                     // Indicates whether the API call was successful or not
    "data": [                            // An array containing the retrieved sync committee participation data
        {
            "participated": <list>,       // List of participation values (1 = participated, 0 = missed) or "no_block_proposed" / "pending"
            "period": <int>,              // Sync committee period
            "slot_number": <int>,         // Slot number of the sync committee participation
            "epoch": <int>,               // Epoch number of the sync committee participation
            "validator_id": <list>,       // List of validator IDs participating in the sync committee
            "participation": <int>,       // Number of validators successfully participated
            "block_timestamp": <datetime> // Timestamp of the corresponding block in ISO 8601 format
        },
        // More sync committee participation entries
    ],
    "range_value": <int>,                // The number of sync committee participation records retrieved
    "from_slot": <int>                   // The starting slot number used for retrieval
}
```

### Notes

-   The `participated` field indicates the participation status of validators. It can be a list of participation indicators or a string ("no_block_proposed," or "pending").
-   The `block_timestamp` field indicates the timestamp of the corresponding slot for each sync committee participation.

### Example

#### Request

```
GET /api/sync_committee_participation/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14&range=5&from_slot=7000000&include_pending=false
```

#### Response

```json
{"success": true, "data": [{"participated": [1], "period": 810, "slot": 6643711, "epoch": 207615, "validator_id": [10], "participation": 506, "block_timestamp": "2023-06-12T05:42:35+00:00"}, {"participated": [1], "period": 810, "slot": 6643710, "epoch": 207615, "validator_id": [10], "participation": 505, "block_timestamp": "2023-06-12T05:42:23+00:00"}, {"participated": [1], "period": 810, "slot": 6643709, "epoch": 207615, "validator_id": [10], "participation": 508, "block_timestamp": "2023-06-12T05:42:11+00:00"}, {"participated": [1], "period": 810, "slot": 6643708, "epoch": 207615, "validator_id": [10], "participation": 506, "block_timestamp": "2023-06-12T05:41:59+00:00"}, {"participated": [1], "period": 810, "slot": 6643707, "epoch": 207615, "validator_id": [10], "participation": 505, "block_timestamp": "2023-06-12T05:41:47+00:00"}], "range_value": 5, "from_slot": 7000000}
```

## API Endpoint `/api/rewards_and_penalties`

### Description

The `/api/rewards_and_penalties` API function allows you to retrieve epoch rewards and penalties data for a specific range of epochs. It provides insights into the rewards and penalties earned by validators for each epoch, including attestation rewards, sync committee rewards, penalties, and other relevant metrics.

### Parameters

1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `range` (optional, default: 5)

The number of epochs for which to retrieve rewards and penalties data. It must be an integer between 1 and 10 (inclusive). If not provided, the default value is 5.

3. `from_epoch` (required)

The starting epoch number for rewards and penalties retrieval. It must be an integer value or "head" to use the latest epoch.

## Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                     // Indicates whether the API call was successful or not
    "data": [                            // An array containing the retrieved rewards and penalties data
        {
            "epoch": <int>,              // Epoch number
            "head": <float>,             // Total head attestations reward
            "target": <float>,           // Total target attestations reward
            "source": <float>,           // Total source attestations reward
            "sync_reward": <float>,      // Total sync committee rewards
            "sync_penalty": <float>,     // Total sync committee penalties (negative value)
            "block_attestations": <float>,// Total block attestations rewards
            "block_sync_aggregate": <float>,// Total block sync aggregate rewards
            "block_proposer_slashings": <float>,// Total block proposer slashings penalties
            "block_attester_slashings": <float>,// Total block attester slashings penalties
            "positive_reward_attestations": <int>,// Number of attestations with positive rewards
            "missed_attestations": <int>,// Number of missed attestations
            "attestation_count": <int>,  // Total number of attestations
            "total_reward": <float>,     // Total rewards earned (sum of all rewards and penalties)
        },
        // More epoch rewards and penalties entries
    ],
    "range_value": <int>,                // The number of epochs retrieved
    "from_epoch": <int>                  // The starting epoch number used for retrieval
}
```

### Notes

- Positive values in the `sync_penalty` field indicate penalties for sync committee participation.
- The `total_reward` field represents the net rewards earned, considering both rewards and penalties.
- This API endpoint is only available for the past 100 epochs (`EPOCH_REWARDS_HISTORY_DISTANCE`). If a epoch before that it queried it returns an empty data array.

### Example

#### Request

```
GET /api/rewards_and_penalties/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14&range=5&from_epoch=220593
```

#### Response


```json
{"success": true, "data": [{"epoch": 220593, "head": 41006, "target": 76342, "source": 41104, "sync_reward": 0, "sync_penalty": 0, "block_attestations": 0, "block_sync_aggregate": 0, "block_proposer_slashings": 0, "block_attester_slashings": 0, "positive_reward_attestations": 14, "missed_attestations": 0, "attestation_count": 14, "total_reward": 158452}, {"epoch": 220592, "head": 41006, "target": 76342, "source": 41090, "sync_reward": 0, "sync_penalty": 0, "block_attestations": 0, "block_sync_aggregate": 0, "block_proposer_slashings": 0, "block_attester_slashings": 0, "positive_reward_attestations": 14, "missed_attestations": 0, "attestation_count": 14, "total_reward": 158438}, {"epoch": 220591, "head": 40698, "target": 76314, "source": 41090, "sync_reward": 0, "sync_penalty": 0, "block_attestations": 0, "block_sync_aggregate": 0, "block_proposer_slashings": 0, "block_attester_slashings": 0, "positive_reward_attestations": 14, "missed_attestations": 0, "attestation_count": 14, "total_reward": 158102}, {"epoch": 220590, "head": 39690, "target": 76272, "source": 41062, "sync_reward": 0, "sync_penalty": 0, "block_attestations": 0, "block_sync_aggregate": 0, "block_proposer_slashings": 0, "block_attester_slashings": 0, "positive_reward_attestations": 14, "missed_attestations": 0, "attestation_count": 14, "total_reward": 157024}, {"epoch": 220589, "head": 40922, "target": 76258, "source": 41062, "sync_reward": 0, "sync_penalty": 0, "block_attestations": 0, "block_sync_aggregate": 0, "block_proposer_slashings": 0, "block_attester_slashings": 0, "positive_reward_attestations": 14, "missed_attestations": 0, "attestation_count": 14, "total_reward": 158242}, {"epoch": 220588, "head": 41034, "target": 76384, "source": 41118, "sync_reward": 0, "sync_penalty": 0, "block_attestations": 0, "block_sync_aggregate": 0, "block_proposer_slashings": 0, "block_attester_slashings": 0, "positive_reward_attestations": 14, "missed_attestations": 0, "attestation_count": 14, "total_reward": 158536}], "range_value": 5, "from_epoch": 220593}
```

## API Endpoint `/api/chart_data`

### Description

The `/api/chart_data` API function enables you to retrieve daily rewards data for a specific range of days, along with corresponding annualized rewards metrics (APY - Annual Percentage Yield). This API is particularly useful for obtaining insights into validator rewards over a specified time period.

### Parameters

1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `range` (optional, default: 5)

The number of days for which to retrieve daily rewards data. It must be an integer between 1 and 90 (inclusive). If not provided, the default value is 5.

3. `from_date` (required)

The starting date for which to retrieve daily rewards data. It must be in the format 'YYYY-MM-DD' or "head" to use the latest date.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                     // Indicates whether the API call was successful or not
    "data": [                            // An array containing the retrieved daily rewards data
        {
            "date": "YYYY-MM-DD",        // Date of the data entry
            "balance_change": <float>,   // Change in total consensus balance (in ETH)
            "execution_reward_change": <float>,// Change in execution rewards (in ETH)
            "missed_attestations_change": <int>,// Change in missed attestations count
            "missed_sync_change": <int>  // Change in missed sync committee count
        },
        // More daily rewards data entries
    ],
    "range_value": <int>,                // The number of days retrieved
    "from_date": "YYYY-MM-DD",           // The starting date used for retrieval
    "apy": [                             // An array containing APY metrics for different timeframes (past day, week and month)
        {
            "execution_reward": <float>, // Total execution rewards (in ETH)
            "consensus_reward": <float>, // Total consensus rewards (in ETH)
            "total_reward": <float>,     // Total rewards (in ETH)
            "consensus_apy": <float>,    // Consensus APY (%)
            "execution_apy": <float>,    // Execution APY (%)
            "apy_sum": <float>,          // Total APY (%)
            "apy": <float>,              // Validator APY (%)
            "missed_attestations": <int>,// Total missed attestations count
            "missed_sync": <int>,        // Total missed sync committee count
            "days": <int>,               // Timeframe in days (past day, week and month)
            "diff": <int>                // Difference in days from the current date
        },
        // More APY metrics entries
    ],
    "total_rewards": {                   // Total rewards data
        "total_execution_reward": <float>,// Total execution rewards (in ETH)
        "total_consensus_reward": <float>,// Total consensus rewards (in ETH)
        "total_reward": <float>          // Total rewards (in ETH)
    }
}
```

### Notes

-   The `balance_change` field represents the change in total consensus balance, which might be a positive or negative number.
-   The `execution_reward_change` field represents the change in execution rewards earned by validators.
-   APY (Annual Percentage Yield) is calculated based on different timeframes (1, 7, and 30 days), considering both execution and consensus rewards.

### Example

#### Request

```
GET /api/chart_data/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14&range=10&from_date=head
```

#### Response

```json
{"success": true, "data": [{"date": "2023-07-31", "balance_change": 0.035406005, "execution_reward_change": 0.0, "missed_attestations_change": 10, "missed_sync_change": 0}, {"date": "2023-08-01", "balance_change": 0.03577356, "execution_reward_change": 0.0, "missed_attestations_change": 1, "missed_sync_change": 0}, {"date": "2023-08-02", "balance_change": 0.035686783, "execution_reward_change": 0.0, "missed_attestations_change": 2, "missed_sync_change": 0}, {"date": "2023-08-03", "balance_change": 0.072728685, "execution_reward_change": 0.010314633883865745, "missed_attestations_change": 3, "missed_sync_change": 0}, {"date": "2023-08-04", "balance_change": 0.03563068, "execution_reward_change": 0.0, "missed_attestations_change": 1, "missed_sync_change": 0}, {"date": "2023-08-05", "balance_change": 0.0353871, "execution_reward_change": 0.0, "missed_attestations_change": 0, "missed_sync_change": 0}, {"date": "2023-08-06", "balance_change": 0.035339723, "execution_reward_change": 0.0, "missed_attestations_change": 2, "missed_sync_change": 0}, {"date": "2023-08-07", "balance_change": 0.035112082, "execution_reward_change": 0.0, "missed_attestations_change": 4, "missed_sync_change": 0}, {"date": "2023-08-08", "balance_change": 0.032614241, "execution_reward_change": 0.0, "missed_attestations_change": 0, "missed_sync_change": 0}], "range_value": 10, "from_epoch": "2023-08-08", "apy": [{"execution_reward": 0.0, "consensus_reward": 0.035112082, "total_reward": 0.035112082, "consensus_apy": 2.8606941808035717, "execution_apy": 0.0, "apy_sum": 12.815909930000002, "apy": 2.8606941808035717, "missed_attestations": 4, "missed_sync": 0, "days": 1, "diff": "2023-08-07", "consensus_apy_sum": 12.815909930000002, "execution_apy_sum": 0.0}, {"execution_reward": 0.010314633883865745, "consensus_reward": 0.285658613, "total_reward": 0.2959732468838657, "consensus_apy": 3.324789341358418, "execution_apy": 0.12005233952841188, "apy_sum": 15.432890730372998, "apy": 3.4448416808868303, "missed_attestations": 13, "missed_sync": 0, "days": 7, "diff": "2023-08-01", "consensus_apy_sum": 14.895056249285714, "execution_apy_sum": 0.5378344810872853}, {"execution_reward": 0.010314633883865745, "consensus_reward": 0.32106461799999997, "total_reward": 0.3313792518838657, "consensus_apy": 0.8719388807291666, "execution_apy": 0.028012212556629435, "apy_sum": 4.031780897920366, "apy": 0.8999510932857959, "missed_attestations": 23, "missed_sync": 0, "days": 30, "diff": "2023-07-09", "consensus_apy_sum": 3.906286185666666, "execution_apy_sum": 0.12549471225369987}], "total_rewards": {"total_execution_reward": 1.6298471595562631, "total_consensus_reward": 69.38109497899995, "total_reward": 71.01094213855622}}
```

## API Endpoint `/api/validators`

### Description

The `/api/validators` API function allows you to retrieve information about validators.

### Parameters

1. `range` (optional, default: 5)

The number of validators to retrieve. It must be an integer between 1 and 100 (inclusive). If not provided, the default value is 5.

2. `cursor` (required)

The starting position in the list of validators. It must be a non-negative integer.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                     // Indicates whether the API call was successful or not
    "data": [                            // An array containing the retrieved validator data
        {
            "public_key": <str>,         // Public key of the validator
            "validator_id": <int>,       // Validator ID
            "activation_epoch": <int>,   // Activation epoch of the validator
            "activation_eligibility_epoch": <int>,// Activation eligibility epoch of the validator
            "exit_epoch": <int>,         // Exit epoch of the validator
            "withdrawable_epoch": <int>, // Withdrawable epoch of the validator
            "status": <str>,             // Current status of the validator (e.g., "active_ongoing", "active_exiting", "active_slashed")
            "balance": <float>,          // Validator balance (in ETH)
            "efficiency": <float>,       // Validator efficiency (percentage)
            "reward": <float>,           // Total validator reward (in ETH)
            "sync_committee_participation_count": <int>,// Count of sync committee participations
            "proposal_count": <int>,     // Total number of proposals by the validator
            "successful_proposals": <int>,// Number of successful proposals by the validator
            "deposited": <float>,        // Deposited amount (in Gwei)
            "pending_validators_queue_ahead": <int>// Number of validators ahead in the pending queue
        },
        // More validator data entries
    ],
    "range_value": <int>,                // The number of validators retrieved
    "cursor": <int>                      // The cursor position used for retrieval
}
```

### Notes

-   The `efficiency` field represents the validator's attestation efficiency as a percentage.
-   The `reward` field represents the total reward earned by the validator, including execution and consensus rewards.
- The `activation_epoch` represents just an estimate when the validator is still pending.

### Example

#### Request

```
GET /api/validators/?range=3&cursor=20
```

#### Response

```json
{"success": true, "data": [{"public_key": "0x942e54850718ce3f6c216795987f6243a73fc5bca395b3e8071a5797ecdf22fc463e75c8537af712f906f47666ae94ce", "validator_id": 870509, "balance": 32.0, "status": "pending_queued", "efficiency": 0.0, "reward": 0.0, "activation_epoch": 227517, "activation_eligibility_epoch": "220577", "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.0, "total_consensus_reward": 0.0, "sync_committee_participation_count": 0, "proposal_count": 0, "successful_proposals": 0, "deposited": 32000000000, "pending_validators_queue_ahead": 69198}, {"public_key": "0x81353c190e577a30382c693b6a2a24fa49c2a0da2f9b4f2c52a857881134020c8e680a9ecbc473c663260bb3fc208751", "validator_id": 870508, "balance": 32.0, "status": "pending_queued", "efficiency": 0.0, "reward": 0.0, "activation_epoch": 227517, "activation_eligibility_epoch": "220577", "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.0, "total_consensus_reward": 0.0, "sync_committee_participation_count": 0, "proposal_count": 0, "successful_proposals": 0, "deposited": 32000000000, "pending_validators_queue_ahead": 69197}, {"public_key": "0xb009e253d65c7fcbbd05c49963bb7f0791f8e968e377507d7a38f3bb2e520c737e952f474a6f9224c7dbd9d5813f877f", "validator_id": 870507, "balance": 32.0, "status": "pending_queued", "efficiency": 0.0, "reward": 0.0, "activation_epoch": 227517, "activation_eligibility_epoch": "220577", "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.0, "total_consensus_reward": 0.0, "sync_committee_participation_count": 0, "proposal_count": 0, "successful_proposals": 0, "deposited": 32000000000, "pending_validators_queue_ahead": 69196}], "range_value": 3, "cursor": 20}
```

## API Endpoint `/api/check_if_proposal_scheduled`

### Description

The `/api/check_if_proposal_scheduled` API function allows you to check if a proposal is scheduled to be made by specified validators during the current epoch.

### Parameters

1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                    // Indicates whether the API call was successful or not
    "proposal_scheduled": <str>,        // Indicates if a proposal is scheduled ("Yes", "No", or "update pending")
    "next_block_not_in": <str>,         // ISO 8601 timestamp when the next proposal is not scheduled (if applicable)
    "next_block_in": <str>              // ISO 8601 timestamp when the next proposal is scheduled (if applicable)
}
```

### Notes

-   The `proposal_scheduled` field indicates whether a proposal is scheduled by the specified validators. Possible values are "Yes" (a proposal is scheduled), "No" (a proposal is not scheduled), or "update pending" (the proposal schedule is pending an update e.g. when a new epoch started).
-   The `next_block_not_in` field provides the ISO 8601 timestamp until no proposal is scheduled. This field is relevant when `proposal_scheduled` is "No".
-   The `next_block_in` field provides the ISO 8601 timestamp when the next proposal is scheduled. This field is relevant when `proposal_scheduled` is "Yes".
-   The `next_block_in` field will be 0 if there is no proposal scheduled (i.e., `proposal_scheduled` is "No" or "update pending").

### Examples

#### Request

```
GET /api/check_if_proposal_scheduled/?validators=123,456
```

#### Response

```json
{
    "success": true,
    "proposal_scheduled": "Yes",
    "next_block_not_in": "2023-08-10T15:30:00Z",
    "next_block_in": "2023-08-10T15:35:00Z"
}
```

#### Request

```
`GET /api/check_if_proposal_scheduled/?validators=789
```

#### Response

```json
{
    "success": true,
    "proposal_scheduled": "No",
    "next_block_not_in": "2023-08-10T16:00:00Z",
    "next_block_in": 0
}
```

#### Request

```
GET /api/check_if_proposal_scheduled/?validators=987
```

#### Response

```json
{
    "success": true,
    "proposal_scheduled": "update pending",
    "next_block_not_in": 0,
    "next_block_in": 0
}
```

## API Endpoint `/api/blocks_by_proposer`

### Description

The `/api/blocks_by_proposer` API function allows you to retrieve blocks proposed by specific validators. This API provides information about blocks including their proposers, block numbers, slot numbers, rewards, and other relevant details.

### Parameters

1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

2. `range`

The number of blocks to retrieve. This parameter is optional and defaults to 5. It must be between 0 and 25.

3. `cursor`

The starting cursor position for fetching blocks. This parameter is optional and defaults to 0. It must be a non-negative integer.

4. `direction`

The direction in which the blocks should be retrieved. This parameter is optional and defaults to "descending". Possible values are "ascending" and "descending".

5. `order_by`

The field by which the blocks should be ordered. This parameter is optional and defaults to "slot". Possible values are "slot" and "total_reward".

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                    // Indicates whether the API call was successful or not
    "data": [
        {
            "proposer": <str>,          // Public key of the proposer validator
            "block_number": <int>,      // Block number
            "slot_number": <int>,       // Slot number
            "fee_recipient": <str>,     // Address of the fee recipient
            "mev_reward_recipient": <str>, // Address of the MEV reward recipient
            "timestamp": <str>,         // ISO 8601 timestamp when the block was proposed
            "total_reward": <float>,    // Total reward in ETH
            "epoch": <int>,             // Epoch of the block
            "mev_boost_relay": <list>,   // MEV boost relay address (if applicable)
            "empty": <bool>             // Indicates if the block is empty (0=successfully proposed, 1=empty/not proposed, 2=orphaned, 3=pending/not processed yet)
        },
        // More block entries...
    ],
    "range_value": <int>,               // Requested range value
    "cursor_value": <int>               // Starting cursor position
}
```

## Notes

-   The `fee_recipient` field indicates the address that receives the transaction fees.
-   The `mev_reward_recipient` field indicates the address that receives the MEV (Miner Extractable Value) rewards.
-   The `mev_boost_relay` field indicates the MEV boost relay/s used if applicable.
-   The `empty` field indicates if the block is empty (0=successfully proposed, 1=empty/not proposed, 2=orphaned, 3=pending/not processed yet)
-   The `timestamp` field is in ISO 8601 format.

### Example

#### Request

```
GET /api/blocks_by_proposer/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14&range=10&cursor=5&direction=ascending&order_by=total_reward
```

#### Response

```json
{"success": true, "data": [{"proposer": 11, "block_number": 15956647, "slot_number": 5122064, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2022-11-12T21:33:11+00:00", "total_reward": 0.004943504501256484, "epoch": 160064, "mev_boost_relay": null, "empty": 0}, {"proposer": 13, "block_number": 15588898, "slot_number": 4752157, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2022-09-22T12:31:47+00:00", "total_reward": 0.005114656906788814, "epoch": 148504, "mev_boost_relay": null, "empty": 0}, {"proposer": 14, "block_number": 16719228, "slot_number": 5889435, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2023-02-27T11:27:23+00:00", "total_reward": 0.005314176055591608, "epoch": 184044, "mev_boost_relay": null, "empty": 0}, {"proposer": 13, "block_number": 15567043, "slot_number": 4730014, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2022-09-19T10:43:11+00:00", "total_reward": 0.005636924252201236, "epoch": 147812, "mev_boost_relay": null, "empty": 0}, {"proposer": 4, "block_number": 17631463, "slot_number": 6815163, "fee_recipient": "0x15f4b914a0ccd14333d850ff311d6dafbfbaa32b", "mev_reward_recipient": "", "timestamp": "2023-07-06T01:12:59+00:00", "total_reward": 0.00629149477849138, "epoch": 212973, "mev_boost_relay": null, "empty": 0}, {"proposer": 5, "block_number": 16600013, "slot_number": 5769007, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2023-02-10T18:01:47+00:00", "total_reward": 0.006732479497311888, "epoch": 180281, "mev_boost_relay": null, "empty": 0}, {"proposer": 11, "block_number": 16867154, "slot_number": 6039193, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2023-03-20T06:38:59+00:00", "total_reward": 0.006811846544393924, "epoch": 188724, "mev_boost_relay": null, "empty": 0}, {"proposer": 5, "block_number": 16087781, "slot_number": 5253953, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2022-12-01T05:10:59+00:00", "total_reward": 0.007419029117608406, "epoch": 164186, "mev_boost_relay": null, "empty": 0}, {"proposer": 13, "block_number": 16458502, "slot_number": 5626678, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2023-01-21T23:35:59+00:00", "total_reward": 0.007755301185518197, "epoch": 175833, "mev_boost_relay": null, "empty": 0}, {"proposer": 13, "block_number": 16272956, "slot_number": 5440193, "fee_recipient": "0xf19b1c91faacf8071bd4bb5ab99db0193809068e", "mev_reward_recipient": "", "timestamp": "2022-12-27T01:58:59+00:00", "total_reward": 0.007829704432888107, "epoch": 170006, "mev_boost_relay": null, "empty": 0}], "range_value": 10, "cursor_value": 5}
```


## API Endpoint `/api/current_beacon_state`

### Description

The `/api/current_beacon_state` API function provides information about the current state of the beacon chain. This includes details about the current epoch, slot, finalized checkpoint, and justified checkpoint.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                          // Indicates whether the API call was successful or not
    "current_epoch": <int>,                   // Current epoch of the beacon chain
    "current_slot": <int>,                    // Current slot number
    "finalized_checkpoint_epoch": <int>,      // Epoch of the finalized checkpoint
    "finalized_checkpoint_root": <str>,       // Root hash of the finalized checkpoint
    "justified_checkpoint_epoch": <int>,      // Epoch of the justified checkpoint
    "justified_checkpoint_root": <str>        // Root hash of the justified checkpoint
}
```

### Example

#### Request

```
GET /api/current_beacon_state
```

#### Response

```json
{"success": true, "current_epoch": 220602, "current_slot": 7059276, "finalized_checkpoint_epoch": 220600, "finalized_checkpoint_root": "0x37d122b96209675be0ef558f489db8cfb95688b30845d7d803fc75c8e99a60fd", "justified_checkpoint_epoch": 220601, "justified_checkpoint_root": "0xd5560c1dc01ba64b95b6b07bc4ff6acc02fff1009cf84c1304f6abd6d375a26a"}
```

## API Endpoint `/api/validators_by_id`

### Description

The `/api/validators_by_id` API function retrieves detailed information about validators based on their unique validator IDs. This information includes attributes such as the validator's public key, activation epoch, withdrawal credentials, efficiency, and more.

### Parameters

1. `validators` (required)

A list of validator IDs for which you want to retrieve attestations. Validator IDs are integer values used to uniquely identify validators.

### Response

The API returns a JSON response with the following structure:

```yaml
{
    "success": true,                         // Indicates whether the API call was successful or not
    "data": [
        {
            "public_key": <str>,              // Public key of the validator
            "validator_id": <int>,            // Id of the validator
            "balance": <float>,               // Current validator balance in ETH
            "status": <str>,                  // Current status of the validator
            "efficiency": <float>,            // Validator's efficiency as a percentage
            "reward": <float>,                // Total reward earned by the validator in ETH
            "activation_epoch": <int>,        // Epoch when the validator was activated
            "activation_eligibility_epoch": <int>, // Epoch when the validator became eligible for activation
            "exit_epoch": <int>,              // Epoch when the validator exited
            "withdrawable_epoch": <int>,      // Epoch when the validator's funds become withdrawable
            "total_execution_reward": <float>, // Total execution reward earned by the validator in ETH
            "total_consensus_reward": <float>, // Total consensus reward earned by the validator in ETH
            "sync_committee_participation_count": <int>, // Number of times validator participated in sync committee
            "proposal_count": <int>,          // Total number of proposals submitted by the validator
            "successful_proposals": <int>,    // Number of successful proposals submitted by the validator
            "deposited": <float>,             // Total deposited amount by the validator
            "pending_validators_queue_ahead": <int> // Number of validators in the activation queue ahead
        },
        // ... additional validator data ...
    ]
}
```

### Notes
- `pending_validators_queue_ahead` is -1 if the validator is not pending.

### Example

#### Request

```
GET /api/validators_by_id/?validators=1,2,3,4,5,6,7,8,9,10,11,12,13,14
```

#### Response

```json
{"success": true, "data": [{"public_key": "0xa1d1ad0714035353258038e964ae9675dc0252ee22cea896825c01458e1807bfad2f9969338798548d9858a571f7425c", "validator_id": 1, "balance": 32.013997937, "status": "active_ongoing", "efficiency": 100.0, "reward": 5.5896049828045, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.23590081080449884, "total_consensus_reward": 5.3537041720000005, "sync_committee_participation_count": 1, "proposal_count": 4, "successful_proposals": 4, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xb2ff4716ed345b05dd1dfc6a5a9fa70856d8c75dcc9e881dd2f766d5f891326f0d10e96f3a444ce6c912b69c22c6754d", "validator_id": 2, "balance": 32.013994621, "status": "active_ongoing", "efficiency": 99.0, "reward": 5.053293850449236, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.056288120449238144, "total_consensus_reward": 4.997005729999998, "sync_committee_participation_count": 0, "proposal_count": 2, "successful_proposals": 2, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0x8e323fd501233cd4d1b9d63d74076a38de50f2f584b001a5ac2412e4e46adb26d2fb2a6041e7e8c57cd4df0916729219", "validator_id": 3, "balance": 32.013901497, "status": "active_ongoing", "efficiency": 97.26, "reward": 5.306681971042015, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.4645823630420172, "total_consensus_reward": 4.842099607999998, "sync_committee_participation_count": 0, "proposal_count": 5, "successful_proposals": 4, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xa62420543ceef8d77e065c70da15f7b731e56db5457571c465f025e032bbcd263a0990c8749b4ca6ff20d77004454b51", "validator_id": 4, "balance": 32.01392927, "status": "active_ongoing", "efficiency": 100.0, "reward": 5.200625703589328, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.1398832725893261, "total_consensus_reward": 5.060742431000001, "sync_committee_participation_count": 0, "proposal_count": 6, "successful_proposals": 6, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xb2ce0f79f90e7b3a113ca5783c65756f96c4b4673c2b5c1eb4efc2228025944106d601211e8866dc5b50dc48a244dd7c", "validator_id": 5, "balance": 36.976943291, "status": "active_ongoing", "efficiency": 100.0, "reward": 5.049665952863791, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.07272266186379323, "total_consensus_reward": 4.976943290999998, "sync_committee_participation_count": 1, "proposal_count": 4, "successful_proposals": 4, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xa16c530143fc72497a85e0de237be174f773cc1e496a94bd13d02708e0fdc1b5c7d25a9c2c05f09d5de8b8ed2bf8e0d2", "validator_id": 6, "balance": 37.004726134, "status": "active_ongoing", "efficiency": 99.17, "reward": 5.067565806590893, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.06283967259089072, "total_consensus_reward": 5.004726134000002, "sync_committee_participation_count": 0, "proposal_count": 3, "successful_proposals": 3, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xa25da1827014cd3bc6e7b70f1375750935a16f00fbe186cc477c204d330cac7ee060b68587c5cdcfae937176a4dd2962", "validator_id": 7, "balance": 36.540908453, "status": "active_ongoing", "efficiency": 99.0, "reward": 4.6112340625543276, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.07032560955432744, "total_consensus_reward": 4.540908453, "sync_committee_participation_count": 0, "proposal_count": 3, "successful_proposals": 3, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0x8078c7f4ab6f9eaaf59332b745be8834434af4ab3c741899abcff93563544d2e5a89acf2bec1eda2535610f253f73ee6", "validator_id": 8, "balance": 36.676978057, "status": "active_ongoing", "efficiency": 98.61, "reward": 4.6769780569999995, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.0, "total_consensus_reward": 4.6769780569999995, "sync_committee_participation_count": 0, "proposal_count": 0, "successful_proposals": 0, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xb016e31f633a21fbe42a015152399361184f1e2c0803d89823c224994af74a561c4ad8cfc94b18781d589d03e952cd5b", "validator_id": 9, "balance": 36.809783612, "status": "active_ongoing", "efficiency": 99.5, "reward": 4.907015216714906, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.09723160471490905, "total_consensus_reward": 4.809783611999997, "sync_committee_participation_count": 0, "proposal_count": 4, "successful_proposals": 4, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0x8efba2238a00d678306c6258105b058e3c8b0c1f36e821de42da7319c4221b77aa74135dab1860235e19d6515575c381", "validator_id": 10, "balance": 37.017653979, "status": "active_ongoing", "efficiency": 99.25, "reward": 5.081777823208669, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.06412384420866722, "total_consensus_reward": 5.017653979000002, "sync_committee_participation_count": 1, "proposal_count": 4, "successful_proposals": 4, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xa2dce641f347a9e46f58458390e168fa4b3a0166d74fc495457cb00c8e4054b5d284c62aa0d9578af1996c2e08e36fb6", "validator_id": 11, "balance": 36.95302546, "status": "active_ongoing", "efficiency": 97.97, "reward": 4.9647808110456495, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.011755351045650408, "total_consensus_reward": 4.953025459999999, "sync_committee_participation_count": 1, "proposal_count": 2, "successful_proposals": 2, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0x98b7d0eac7ab95d34dbf2b7baa39a8ec451671328c063ab1207c2055d9d5d6f1115403dc5ea19a1111a404823bd9a6e9", "validator_id": 12, "balance": 36.732015526, "status": "active_ongoing", "efficiency": 97.42, "reward": 4.732708465395606, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.000692939395608297, "total_consensus_reward": 4.732015525999998, "sync_committee_participation_count": 0, "proposal_count": 1, "successful_proposals": 1, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xb0fd08e2e06d1f4d90d0d6843feb543ebeca684cde397fe230e6cdf6f255d234f2c26f4b36c07170dfdfcbbe355d0848", "validator_id": 13, "balance": 37.367646391, "status": "active_ongoing", "efficiency": 100.0, "reward": 5.614374368146791, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.24672797714678982, "total_consensus_reward": 5.367646391000001, "sync_committee_participation_count": 1, "proposal_count": 12, "successful_proposals": 12, "deposited": 32000000000, "pending_validators_queue_ahead": -1}, {"public_key": "0xab7a5aa955382906be3d76e322343bd439e8690f286ecf2f2a7646363b249f5c133d0501d766ccf1aa1640f0283047b3", "validator_id": 14, "balance": 37.049103197, "status": "active_ongoing", "efficiency": 100.0, "reward": 5.155876129150547, "activation_epoch": 0, "activation_eligibility_epoch": 0, "exit_epoch": 18446744073709551615, "withdrawable_epoch": 18446744073709551615, "total_execution_reward": 0.10677293215054667, "total_consensus_reward": 5.049103197000001, "sync_committee_participation_count": 1, "proposal_count": 6, "successful_proposals": 6, "deposited": 32000000000, "pending_validators_queue_ahead": -1}]}
```

/*
 * Copyright (c) 2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

typedef union {
    uint32_t data;
    struct {
        uint8_t y;
        uint8_t x;
        uint8_t y_size;
        uint8_t x_size;
    };
    struct {
        uint16_t p2p_addr;
        uint16_t p2p_dims;
    };
} p2p_data_t;

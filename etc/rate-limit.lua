--
-- Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
-- Licensed under the GPL-3.0: https://www.gnu.org/licenses/gpl-3.0.txt
--

local function getenv(var_name, default)
    local value = os.getenv(var_name)
    if value == nil then
        return default
    end

    -- WARNING: explicitly convert to a number
    return tonumber(value)
end

local function startswith(self, start)
    return self:sub(1, #start) == start
end

-- REMEMBER: these are per IP address, not total
-- Configuration values
-- key = zone-name, rate/s, burst/s
local LIMITS = {
    authenticated = {
        "limit_storage_authenticated",
        getenv("NGX_AUTHENTICATED_RATE",  300),
        getenv("NGX_AUTHENTICATED_BURST", 100),
    },

    errors = {
        "limit_storage_errors",
        getenv("NGX_ERRORS_RATE",  0.02), -- 1r/m
        getenv("NGX_ERRORS_BURST", 1),
    },

    -- WARNING: limits for static files should be much higher than /acounts/login/
    -- and other authenticated requests otherwise may block the client and
    -- result in the entire page being rate limited
    static = {
        "limit_storage_static",
        getenv("NGX_STATIC_RATE",  300),
        getenv("NGX_STATIC_BURST", 100),
    },

    uploads = {
        "limit_storage_uploads",
        getenv("NGX_UPLOADS_RATE",  10),
        getenv("NGX_UPLOADS_BURST", 10),
    },
}

-- WARNING: must be the same as limit_req_status in Nginx
-- otherwise our testing tools will count wrong
local NGX_LIMIT_REQ_STATUS = 429

-- WARNING: should always be set but error check anyway
local config_key = ngx.var.rate_limit_config_key
if LIMITS[config_key] == nil then
    ngx.log(ngx.ERR, "Cannot find rate limit configuration for: ", ngx.var.request_uri)
    -- don't crash everything in case we have an error in the rate-limit config
    return
end

local ZONE_NAME, RATE, BURST = table.unpack(LIMITS[config_key])
local limit_module = require "resty.limit.req"

local bucket, err = limit_module.new(ZONE_NAME, RATE, BURST)
if not bucket then
    ngx.log(ngx.ERR,
            "Failed to instantiate a resty.limit.req object: ", err)
    return ngx.exit(500)
end

-- the following call must be per-request.
local delay, err = bucket:incoming(ngx.var.binary_remote_addr, true)
if not delay then
    if err == "rejected" then
        return ngx.exit(NGX_LIMIT_REQ_STATUS)
    end
    ngx.log(ngx.ERR, "Failed to limit request: ", err)
    return ngx.exit(500)
end

-- NOTE: we operate in a no-delay fashion for now
-- if delay >= 0.001 then
    -- the 2nd return value holds the number of excess requests
    -- per second for the specified key. for example, number 31
    -- means the current request rate is at 231 req/sec for the
    -- specified key.
    -- local excess = err

    -- the request exceeding the 200 req/sec but below 300 req/sec,
    -- so we intentionally delay it here a bit to conform to the
    -- 200 req/sec rate.
--     ngx.sleep(delay)
-- end

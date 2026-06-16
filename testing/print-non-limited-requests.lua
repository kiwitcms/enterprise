-- Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
--
-- Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
-- https://www.gnu.org/licenses/agpl-3.0.html

response = function(status, headers, body)
    if status ~= 429 then
        print("non-429 request status=", status, "\n")
    end
end

// In src/js/signup.js, after successful signup, keep this behavior:
//
// sessionStorage.setItem("icaro_ops_company", JSON.stringify(body));
// window.location.href = "index.html";
//
// The dashboard map reads the company_id from sessionStorage and loads the HQ/base marker.
// No aircraft marker is drawn until company_aircraft records exist in future patches.

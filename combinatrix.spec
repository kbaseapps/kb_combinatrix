/*
A KBase module: combinatrix
*/

module combinatrix {

    /* a workspace id */
    typedef int ws_id;

    /* a workspace object reference string (of the form wsid/objid/ver) */
    typedef string ws_ref;

    /* output from the KBaseReport app */
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /* dataset join information as specified in the UI */
    typedef structure {
        ws_ref t1_ref;
        ws_ref t2_ref;
        string t1_field;
        string t2_field;
    } JoinSpec;

    /* input params for the Combinatrix */
    typedef structure {
        list<JoinSpec> join_list;
        ws_id workspace_id;
    } CombinatrixParams;

    /*

        Run the Combinatrix to produce a report detailing all possible combinations of the inputs.

    */

    funcdef run_combinatrix(CombinatrixParams params) returns (ReportResults output) authentication required;

};

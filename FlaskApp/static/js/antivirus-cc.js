function view_data(data)  {
    //SORTING
	function sortFunction(a, b){
		var value1 = data[a];
        var value2 = data[b];
            
		return ((value1 > value2) ? -1 : ((value1 > value2) ? 1 : 0));
    }
    
    sorted_av_list = []
    for(av_copy in data)  {
		sorted_av_list.push(av_copy);
    }
    sorted_av_list.sort(sortFunction);

    for(i in sorted_av_list)  {
        var copy = sorted_av_list[i];
        var av_copier = copy.split('->')[0];
        var av_copied = copy.split('->')[1];

        html_to_add = "<tr role=\"row\"><td>" + av_copier + " -> " + av_copied + "</td>";
        html_to_add += "<td>" + data[copy] + "</td></tr>";
        $("tbody").append(html_to_add);
    }
};